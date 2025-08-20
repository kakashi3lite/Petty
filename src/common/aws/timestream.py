"""
AWS Timestream helpers with retries and backoff for telemetry data.
"""

import os
import time
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

_TIMESTREAM_CLIENT = None


def _get_timestream_client():
    """Get singleton Timestream write client."""
    global _TIMESTREAM_CLIENT
    if _TIMESTREAM_CLIENT is None:
        _TIMESTREAM_CLIENT = boto3.client(
            'timestream-write',
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            config=boto3.session.Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                max_pool_connections=50
            )
        )
    return _TIMESTREAM_CLIENT


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=5),
    retry=retry_if_exception_type((ClientError, BotoCoreError))
)
def write_records(database: str, table: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Write records to Timestream with retries and backoff.
    
    Args:
        database: Timestream database name
        table: Timestream table name  
        records: List of Timestream record dictionaries
        
    Returns:
        Timestream write response
        
    Raises:
        Exception: If write fails after retries
    """
    try:
        client = _get_timestream_client()
        response = client.write_records(
            DatabaseName=database,
            TableName=table,
            Records=records
        )
        
        logger.debug(
            "Successfully wrote records to Timestream",
            extra={
                "database": database,
                "table": table,
                "record_count": len(records)
            }
        )
        
        return response
        
    except (ClientError, BotoCoreError) as e:
        logger.error(
            "Failed to write records to Timestream",
            extra={
                "database": database,
                "table": table,
                "record_count": len(records),
                "error": str(e)
            }
        )
        raise


def query_last_24h(collar_id: str, database: str = None, table: str = None) -> List[Dict[str, Any]]:
    """
    Query last 24 hours of telemetry data for a collar.
    
    Args:
        collar_id: Collar identifier
        database: Optional database name (defaults to env var)
        table: Optional table name (defaults to env var)
        
    Returns:
        List of telemetry data dictionaries in DATA_PROTOCOL format
    """
    database = database or os.getenv("TIMESTREAM_DATABASE", "PettyDB")
    table = table or os.getenv("TIMESTREAM_TABLE", "CollarMetrics")
    
    # Get Timestream query client (different from write client)
    query_client = boto3.client(
        'timestream-query',
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    
    # Query last 24 hours in ascending order
    query = f"""
    SELECT 
        CollarId,
        time,
        measure_value::double as HeartRate,
        measure_value::bigint as ActivityLevel,
        measure_value::double as Longitude,
        measure_value::double as Latitude
    FROM "{database}"."{table}"
    WHERE CollarId = '{collar_id}'
        AND time >= ago(24h)
    ORDER BY time ASC
    """
    
    try:
        response = query_client.query(QueryString=query)
        
        # Convert Timestream response to DATA_PROTOCOL format
        telemetry_data = []
        rows = response.get('Rows', [])
        
        for row in rows:
            data = row.get('Data', [])
            if len(data) >= 6:
                # Map to DATA_PROTOCOL dict shape
                telemetry_data.append({
                    "collar_id": data[0].get('ScalarValue', collar_id),
                    "timestamp": data[1].get('ScalarValue', ''),
                    "heart_rate": int(float(data[2].get('ScalarValue', 0))),
                    "activity_level": int(data[3].get('ScalarValue', 0)),
                    "location": {
                        "type": "Point",
                        "coordinates": [
                            float(data[4].get('ScalarValue', 0)),  # longitude
                            float(data[5].get('ScalarValue', 0))   # latitude
                        ]
                    }
                })
        
        logger.debug(
            "Successfully queried Timestream data",
            extra={
                "collar_id": collar_id,
                "record_count": len(telemetry_data)
            }
        )
        
        return telemetry_data
        
    except Exception as e:
        logger.error(
            "Failed to query Timestream data",
            extra={
                "collar_id": collar_id,
                "database": database,
                "table": table,
                "error": str(e)
            }
        )
        raise