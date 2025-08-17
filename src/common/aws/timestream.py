"""
AWS Timestream utilities for querying telemetry data.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import boto3
from botocore.exceptions import ClientError, BotoCoreError

# Environment configuration
TIMESTREAM_DATABASE = os.getenv("TIMESTREAM_DATABASE", "PettyDB")
TIMESTREAM_TABLE = os.getenv("TIMESTREAM_TABLE", "CollarMetrics")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

logger = logging.getLogger(__name__)

def _get_timestream_query_client():
    """Get configured Timestream query client"""
    session = boto3.Session()
    return session.client(
        'timestream-query',
        region_name=AWS_REGION,
        config=boto3.session.Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50
        )
    )

def query_last_24h(collar_id: str) -> List[Dict[str, Any]]:
    """
    Query the last 24 hours of telemetry data from Timestream for a specific collar.
    
    Args:
        collar_id: Collar identifier to query data for
        
    Returns:
        List of telemetry records in the DATA_PROTOCOL format:
        {
            "collar_id": str,
            "timestamp": str (ISO format),
            "heart_rate": int,
            "activity_level": int,
            "location": {"type": "Point", "coordinates": [lon, lat]}
        }
        
    Raises:
        Exception: If query fails or data cannot be retrieved
    """
    client = _get_timestream_query_client()
    
    # Calculate 24 hours ago
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=24)
    
    # Query with the correct structure for MULTI measure values
    query = f"""
    SELECT 
        CollarId,
        time,
        measure_name,
        measure_value::double
    FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
    WHERE CollarId = '{collar_id}' 
        AND time >= ago(24h)
    ORDER BY time ASC
    """
    
    try:
        # Execute the query
        response = client.query(QueryString=query)
        
        # Process the results and transform to our canonical format
        telemetry_data = []
        rows = response.get('Rows', [])
        
        # Group rows by time since Timestream returns separate rows for each measure
        time_groups = {}
        
        for row in rows:
            data = row.get('Data', [])
            if len(data) >= 4:
                collar_id_val = data[0].get('ScalarValue', '')
                timestamp_val = data[1].get('ScalarValue', '')
                measure_name = data[2].get('ScalarValue', '')
                measure_value = data[3].get('ScalarValue', '')
                
                # Initialize time group if not exists
                if timestamp_val not in time_groups:
                    time_groups[timestamp_val] = {
                        'collar_id': collar_id_val,
                        'timestamp': timestamp_val,
                        'heart_rate': None,
                        'activity_level': None,
                        'longitude': None,
                        'latitude': None
                    }
                
                # Assign values based on measure name
                if measure_name == 'HeartRate':
                    time_groups[timestamp_val]['heart_rate'] = int(float(measure_value))
                elif measure_name == 'ActivityLevel':
                    time_groups[timestamp_val]['activity_level'] = int(float(measure_value))
                elif measure_name == 'Longitude':
                    time_groups[timestamp_val]['longitude'] = float(measure_value)
                elif measure_name == 'Latitude':
                    time_groups[timestamp_val]['latitude'] = float(measure_value)
        
        # Convert grouped data to the expected format
        for timestamp, data in time_groups.items():
            if all(data[key] is not None for key in ['heart_rate', 'activity_level', 'longitude', 'latitude']):
                # Convert timestamp to ISO format if needed
                try:
                    # Parse Timestream timestamp format and convert to ISO
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    iso_timestamp = dt.isoformat().replace('+00:00', 'Z')
                except:
                    iso_timestamp = timestamp
                
                telemetry_data.append({
                    "collar_id": data['collar_id'],
                    "timestamp": iso_timestamp,
                    "heart_rate": data['heart_rate'],
                    "activity_level": data['activity_level'],
                    "location": {
                        "type": "Point",
                        "coordinates": [data['longitude'], data['latitude']]
                    }
                })
        
        # Sort by timestamp
        telemetry_data.sort(key=lambda x: x['timestamp'])
        
        logger.info(
            f"Retrieved {len(telemetry_data)} telemetry records for collar {collar_id}"
        )
        
        return telemetry_data
        
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Timestream query failed for collar {collar_id}: {e}")
        raise Exception(f"Failed to query Timestream: {e}")
    except Exception as e:
        logger.error(f"Unexpected error querying Timestream for collar {collar_id}: {e}")
        raise