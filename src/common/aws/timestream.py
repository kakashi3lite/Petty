"""
AWS Timestream helper for writing telemetry records with retries and backoff.
"""

import time
from typing import Dict, List, Any, Optional
import logging

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    # Mock classes for when boto3 is not available
    class ClientError(Exception):
        pass
    class BotoCoreError(Exception):
        pass
    # Mock retry decorator when tenacity is not available
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = lambda x: None
    wait_exponential = lambda **kwargs: None
    retry_if_exception_type = lambda x: None

logger = logging.getLogger(__name__)

class TimestreamWriter:
    """AWS Timestream writer with retry logic and best practices."""
    
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Timestream writer.
        
        Args:
            region_name: AWS region for Timestream service
        """
        self.region_name = region_name
        self._client: Optional[Any] = None
        
    @property
    def client(self) -> Any:
        """Lazy initialization of Timestream client."""
        if self._client is None:
            if not BOTO3_AVAILABLE:
                raise ImportError("boto3 is required for Timestream operations")
            
            self._client = boto3.client(
                'timestream-write',
                region_name=self.region_name,
                config=boto3.session.Config(
                    retries={'max_attempts': 3, 'mode': 'adaptive'},
                    max_pool_connections=50
                )
            )
        return self._client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError)),
        reraise=True
    )
    def write_records(self, database: str, table: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Write records to AWS Timestream with retries and exponential backoff.
        
        Args:
            database: Timestream database name
            table: Timestream table name  
            records: List of Timestream record dictionaries
            
        Returns:
            Timestream write response
            
        Raises:
            ClientError: For AWS API errors
            BotoCoreError: For boto3 connection errors
            ValueError: For invalid input parameters
        """
        if not database:
            raise ValueError("Database name is required")
        if not table:
            raise ValueError("Table name is required")
        if not records or not isinstance(records, list):
            raise ValueError("Records must be a non-empty list")
        
        try:
            # Write to Timestream
            response = self.client.write_records(
                DatabaseName=database,
                TableName=table,
                Records=records
            )
            
            logger.debug(
                "Successfully wrote records to Timestream",
                extra={
                    "database": database,
                    "table": table,
                    "record_count": len(records),
                    "rejected_records": len(response.get("RejectedRecords", []))
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
                    "error": str(e),
                    "error_code": getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
                }
            )
            raise


def build_collar_record(collar_id: str, timestamp: str, heart_rate: int, 
                       activity_level: int, location: Dict[str, Any], 
                       environment: str = "development") -> Dict[str, Any]:
    """
    Build a Timestream record from collar telemetry data.
    
    Args:
        collar_id: Unique collar identifier
        timestamp: ISO8601 timestamp or Unix timestamp in milliseconds  
        heart_rate: Heart rate measurement
        activity_level: Activity level (0=rest, 1=moderate, 2=active)
        location: GeoJSON Point with coordinates [longitude, latitude]
        environment: Environment identifier (development, staging, production)
        
    Returns:
        Timestream record dictionary
        
    Raises:
        ValueError: For invalid input parameters
    """
    # Validate inputs
    if not collar_id or not isinstance(collar_id, str):
        raise ValueError("collar_id must be a non-empty string")
    
    if not isinstance(heart_rate, int) or not (30 <= heart_rate <= 300):
        raise ValueError("heart_rate must be an integer between 30 and 300")
    
    if not isinstance(activity_level, int) or activity_level not in [0, 1, 2]:
        raise ValueError("activity_level must be 0, 1, or 2")
    
    if not isinstance(location, dict) or location.get('type') != 'Point':
        raise ValueError("location must be a GeoJSON Point")
    
    coordinates = location.get('coordinates', [])
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        raise ValueError("location coordinates must be [longitude, latitude]")
    
    longitude, latitude = coordinates
    if not isinstance(longitude, (int, float)) or not isinstance(latitude, (int, float)):
        raise ValueError("coordinates must be numeric")
    
    if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
        raise ValueError("coordinates out of valid range")
    
    # Handle timestamp - convert to milliseconds since epoch if needed
    if isinstance(timestamp, str):
        try:
            # Try parsing ISO8601 format
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_ms = str(int(dt.timestamp() * 1000))
        except (ValueError, ImportError):
            # Fallback to current time
            time_ms = str(int(time.time() * 1000))
    else:
        # Assume it's already in milliseconds
        time_ms = str(int(timestamp))
    
    # Build the Timestream record
    record = {
        'Time': time_ms,
        'TimeUnit': 'MILLISECONDS',
        'Dimensions': [
            {
                'Name': 'CollarId',
                'Value': str(collar_id),
                'DimensionValueType': 'VARCHAR'
            },
            {
                'Name': 'Environment',
                'Value': str(environment),
                'DimensionValueType': 'VARCHAR'
            }
        ],
        'MeasureName': 'CollarMetrics',
        'MeasureValueType': 'MULTI',
        'MeasureValues': [
            {
                'Name': 'HeartRate',
                'Value': str(heart_rate),
                'Type': 'DOUBLE'
            },
            {
                'Name': 'ActivityLevel',
                'Value': str(activity_level),
                'Type': 'BIGINT'
            },
            {
                'Name': 'Longitude',
                'Value': str(longitude),
                'Type': 'DOUBLE'
            },
            {
                'Name': 'Latitude',
                'Value': str(latitude),
                'Type': 'DOUBLE'
            }
        ]
    }
    
    return record


# Global writer instance - will be lazily initialized
_writer: Optional[TimestreamWriter] = None

def get_timestream_writer(region_name: str = "us-east-1") -> TimestreamWriter:
    """Get or create global TimestreamWriter instance."""
    global _writer
    if _writer is None:
        _writer = TimestreamWriter(region_name)
    return _writer


def write_records(database: str, table: str, records: List[Dict[str, Any]], 
                 region_name: str = "us-east-1") -> Dict[str, Any]:
    """
    Convenience function to write records to Timestream.
    
    Args:
        database: Timestream database name
        table: Timestream table name
        records: List of Timestream record dictionaries
        region_name: AWS region name
        
    Returns:
        Timestream write response
    """
    writer = get_timestream_writer(region_name)
    return writer.write_records(database, table, records)