"""
AWS Timestream helper functions with retries and backoff
"""

import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from aws_lambda_powertools import Logger
    logger = Logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def _get_timestream_client():
    """Get or create Timestream write client"""
    return boto3.client('timestream-write')


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((ClientError, BotoCoreError))
)
def write_records(database: str, table: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Write records to AWS Timestream with retries and backoff.
    
    Args:
        database: Timestream database name
        table: Timestream table name  
        records: List of record dictionaries with dimensions and measures
        
    Returns:
        Response from Timestream WriteRecords API
        
    Raises:
        ClientError: If AWS API call fails after retries
        ValueError: If records format is invalid
    """
    if not records:
        raise ValueError("Records list cannot be empty")
    
    client = _get_timestream_client()
    
    try:
        response = client.write_records(
            DatabaseName=database,
            TableName=table,
            Records=records
        )
        
        logger.info(
            "Successfully wrote records to Timestream",
            database=database,
            table=table,
            record_count=len(records),
            request_id=response.get('ResponseMetadata', {}).get('RequestId')
        )
        
        return response
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(
            "Failed to write records to Timestream",
            database=database,
            table=table,
            record_count=len(records),
            error_code=error_code,
            error_message=str(e)
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error writing to Timestream",
            database=database,
            table=table,
            record_count=len(records),
            error=str(e)
        )
        raise


def build_timestream_record(
    collar_id: str,
    timestamp: str,
    heart_rate: int,
    activity_level: int,
    location: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a properly formatted Timestream record from collar data.
    
    Args:
        collar_id: Collar identifier (e.g., "SN-12345")
        timestamp: ISO8601 timestamp string
        heart_rate: Heart rate in BPM
        activity_level: Activity level (0=rest, 1=active, 2=high)
        location: GeoJSON Point object
        
    Returns:
        Timestream record dictionary
    """
    # Parse timestamp to ensure it's valid
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_value = str(int(dt.timestamp() * 1000))  # Convert to milliseconds
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {timestamp}") from e
    
    # Validate location is GeoJSON Point
    if not isinstance(location, dict) or location.get('type') != 'Point':
        raise ValueError("Location must be a GeoJSON Point object")
    
    coordinates = location.get('coordinates', [])
    if len(coordinates) != 2:
        raise ValueError("GeoJSON Point coordinates must have exactly 2 values")
    
    longitude, latitude = coordinates
    
    # Build Timestream record
    record = {
        'Time': time_value,
        'TimeUnit': 'MILLISECONDS',
        'Dimensions': [
            {
                'Name': 'collar_id',
                'Value': collar_id,
                'DimensionValueType': 'VARCHAR'
            }
        ],
        'MeasureName': 'collar_metrics',
        'MeasureValueType': 'MULTI',
        'MeasureValues': [
            {
                'Name': 'heart_rate',
                'Value': str(heart_rate),
                'Type': 'BIGINT'
            },
            {
                'Name': 'activity_level',
                'Value': str(activity_level),
                'Type': 'BIGINT'
            },
            {
                'Name': 'longitude',
                'Value': str(longitude),
                'Type': 'DOUBLE'
            },
            {
                'Name': 'latitude',
                'Value': str(latitude),
                'Type': 'DOUBLE'
            }
        ]
    }
    
    return record


def query_last_24h(collar_id: str, database: str = "PettyDB", table: str = "CollarMetrics") -> List[Dict[str, Any]]:
    """
    Query last 24 hours of telemetry data for a collar.
    
    Args:
        collar_id: Collar identifier
        database: Timestream database name
        table: Timestream table name
        
    Returns:
        List of telemetry data dictionaries in DATA_PROTOCOL format
    """
    client = boto3.client('timestream-query')
    
    query = f"""
    SELECT collar_id, time, measure_name, measure_value::double as measure_value
    FROM "{database}"."{table}"
    WHERE collar_id = '{collar_id}'
      AND time >= ago(24h)
    ORDER BY time ASC
    """
    
    try:
        response = client.query(QueryString=query)
        
        # Group results by timestamp
        records_by_time = {}
        
        for row in response.get('Rows', []):
            data = {col['Name']: col['Data']['ScalarValue'] for col in row['Data']}
            timestamp = data['time']
            
            if timestamp not in records_by_time:
                records_by_time[timestamp] = {
                    'collar_id': data['collar_id'],
                    'timestamp': timestamp,
                    'heart_rate': None,
                    'activity_level': None,
                    'location': {'type': 'Point', 'coordinates': [None, None]}
                }
            
            measure_name = data['measure_name']
            measure_value = data['measure_value']
            
            if measure_name == 'heart_rate':
                records_by_time[timestamp]['heart_rate'] = int(float(measure_value))
            elif measure_name == 'activity_level':
                records_by_time[timestamp]['activity_level'] = int(float(measure_value))
            elif measure_name == 'longitude':
                records_by_time[timestamp]['location']['coordinates'][0] = float(measure_value)
            elif measure_name == 'latitude':
                records_by_time[timestamp]['location']['coordinates'][1] = float(measure_value)
        
        # Convert to list and filter complete records
        telemetry_data = []
        for record in records_by_time.values():
            if (record['heart_rate'] is not None and 
                record['activity_level'] is not None and
                all(coord is not None for coord in record['location']['coordinates'])):
                telemetry_data.append(record)
        
        logger.info(
            "Successfully queried Timestream data",
            collar_id=collar_id,
            record_count=len(telemetry_data)
        )
        
        return telemetry_data
        
    except ClientError as e:
        logger.error(
            "Failed to query Timestream",
            collar_id=collar_id,
            error_code=e.response.get('Error', {}).get('Code', 'Unknown'),
            error_message=str(e)
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error querying Timestream",
            collar_id=collar_id,
            error=str(e)
        )
        raise