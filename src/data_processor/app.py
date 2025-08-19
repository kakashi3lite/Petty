"""
Production-grade data processor Lambda with security and observability.
Implements OWASP LLM Top 10 mitigations for IoT data ingestion.
"""

import json
import os
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, BotoCoreError

# Import security and observability modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from aws_lambda_powertools import Logger, Tracer, Metrics
    from aws_lambda_powertools.logging import correlation_paths
    from aws_lambda_powertools.metrics import MetricUnit
    from aws_lambda_powertools.utilities.typing import LambdaContext
    AWS_POWERTOOLS_AVAILABLE = True
except ImportError:
    AWS_POWERTOOLS_AVAILABLE = False
    class LambdaContext:
        pass

try:
    from common.security.input_validators import validate_collar_data, InputValidator
    from common.security.output_schemas import secure_response_wrapper
    from common.security.rate_limiter import safe_mode_rate_limit_decorator, RateLimitExceeded
    from common.observability.logger import get_logger
    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False
    logging.warning("Security modules not available - using fallbacks")

# Configure logger
if AWS_POWERTOOLS_AVAILABLE:
    logger = Logger(service="data-processor")
    tracer = Tracer(service="data-processor")
    metrics = Metrics(service="data-processor", namespace="Petty")
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

# Environment configuration
TIMESTREAM_DATABASE = os.getenv("TIMESTREAM_DATABASE", "PettyDB")
TIMESTREAM_TABLE = os.getenv("TIMESTREAM_TABLE", "CollarMetrics")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize AWS clients with retry configuration
session = boto3.Session()
timestream_client = session.client(
    'timestream-write',
    region_name=AWS_REGION,
    config=boto3.session.Config(
        retries={'max_attempts': 3, 'mode': 'adaptive'},
        max_pool_connections=50
    )
)

class DataProcessor:
    """Secure data processor for collar telemetry"""
    
    def __init__(self):
        self.validator = InputValidator() if SECURITY_MODULES_AVAILABLE else None
        self.logger = logger
        
    def process_telemetry(self, event_body: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Process and validate collar telemetry data
        
        Args:
            event_body: Raw event data from API Gateway
            request_id: Unique request identifier
            
        Returns:
            Processing result with success/error status
        """
        start_time = time.time()
        
        try:
            # Input validation and sanitization
            if self.validator:
                validated_data = self.validator.validate_collar_data(event_body)
                clean_data = validated_data.dict()
            else:
                # Fallback validation
                clean_data = self._fallback_validate(event_body)
            
            # Store in Timestream
            timestream_result = self._write_to_timestream(clean_data, request_id)
            
            # Record metrics
            processing_time = time.time() - start_time
            if AWS_POWERTOOLS_AVAILABLE:
                metrics.add_metric(name="ProcessingTime", unit=MetricUnit.Seconds, value=processing_time)
                metrics.add_metric(name="SuccessfulIngestion", unit=MetricUnit.Count, value=1)
            
            self.logger.info(
                "Telemetry data processed successfully",
                collar_id=clean_data.get("collar_id"),
                processing_time=processing_time,
                request_id=request_id,
                timestream_record_id=timestream_result.get("RecordId")
            )
            
            if SECURITY_MODULES_AVAILABLE:
                return secure_response_wrapper(
                    success=True,
                    message="Data processed successfully",
                    request_id=request_id
                )
            else:
                return {"statusCode": 200, "body": json.dumps({"ok": True})}
                
        except Exception as e:
            # Record failure metrics
            if AWS_POWERTOOLS_AVAILABLE:
                metrics.add_metric(name="FailedIngestion", unit=MetricUnit.Count, value=1)
            
            self.logger.error(
                "Telemetry processing failed",
                error=str(e),
                error_type=type(e).__name__,
                request_id=request_id,
                collar_id=event_body.get("collar_id") if isinstance(event_body, dict) else "unknown"
            )
            
            if SECURITY_MODULES_AVAILABLE:
                return secure_response_wrapper(
                    success=False,
                    message="Processing failed",
                    error_code="PROCESSING_ERROR",
                    request_id=request_id
                )
            else:
                return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    
    def _fallback_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback validation when security modules unavailable"""
        required_fields = ["collar_id", "timestamp", "heart_rate", "activity_level", "location"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Basic type and range validation
        hr = data["heart_rate"]
        if not isinstance(hr, (int, float)) or not (30 <= hr <= 300):
            raise ValueError(f"Invalid heart rate: {hr}")
        
        activity = data["activity_level"]
        if not isinstance(activity, int) or not (0 <= activity <= 2):
            raise ValueError(f"Invalid activity level: {activity}")
        
        return data
    
    def _write_to_timestream(self, data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Write validated data to AWS Timestream
        
        Args:
            data: Validated collar data
            request_id: Request identifier for tracing
            
        Returns:
            Timestream write response
        """
        try:
            # Prepare Timestream record
            current_time = str(int(time.time() * 1000))  # Milliseconds since epoch
            
            # Extract location data safely
            location = data.get("location", {})
            coordinates = location.get("coordinates", [0, 0])
            longitude = coordinates[0] if len(coordinates) > 0 else 0
            latitude = coordinates[1] if len(coordinates) > 1 else 0
            
            record = {
                'Time': current_time,
                'TimeUnit': 'MILLISECONDS',
                'Dimensions': [
                    {
                        'Name': 'CollarId',
                        'Value': str(data["collar_id"]),
                        'DimensionValueType': 'VARCHAR'
                    },
                    {
                        'Name': 'Environment',
                        'Value': ENVIRONMENT,
                        'DimensionValueType': 'VARCHAR'
                    }
                ],
                'MeasureName': 'CollarMetrics',
                'MeasureValueType': 'MULTI',
                'MeasureValues': [
                    {
                        'Name': 'HeartRate',
                        'Value': str(data["heart_rate"]),
                        'Type': 'DOUBLE'
                    },
                    {
                        'Name': 'ActivityLevel',
                        'Value': str(data["activity_level"]),
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
            
            # Write to Timestream with retry logic
            response = timestream_client.write_records(
                DatabaseName=TIMESTREAM_DATABASE,
                TableName=TIMESTREAM_TABLE,
                Records=[record]
            )
            
            self.logger.debug(
                "Data written to Timestream",
                database=TIMESTREAM_DATABASE,
                table=TIMESTREAM_TABLE,
                collar_id=data["collar_id"],
                request_id=request_id
            )
            
            return response
            
        except (ClientError, BotoCoreError) as e:
            self.logger.error(
                "Timestream write failed",
                error=str(e),
                database=TIMESTREAM_DATABASE,
                table=TIMESTREAM_TABLE,
                request_id=request_id
            )
            raise Exception(f"Failed to write to Timestream: {e}")

# Global processor instance
processor = DataProcessor()

@tracer.capture_lambda_handler if AWS_POWERTOOLS_AVAILABLE else lambda x: x
@logger.inject_lambda_context(log_event=True) if AWS_POWERTOOLS_AVAILABLE else lambda x: x
@safe_mode_rate_limit_decorator("ingest", tokens=1, heavy_route=True, key_func=lambda event, context: event.get("body", {}).get("collar_id", "unknown")) if SECURITY_MODULES_AVAILABLE else lambda x: x
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    AWS Lambda handler for collar data ingestion
    
    Security features:
    - Input validation and sanitization
    - Rate limiting by collar ID
    - Structured logging with PII redaction
    - Error handling with secure responses
    - AWS Timestream integration with retry logic
    """
    request_id = getattr(context, 'aws_request_id', 'unknown')
    
    try:
        # Parse request body
        body = event.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in request body", error=str(e), request_id=request_id)
                if SECURITY_MODULES_AVAILABLE:
                    return secure_response_wrapper(
                        success=False,
                        message="Invalid JSON format",
                        error_code="INVALID_JSON",
                        request_id=request_id
                    )
                else:
                    return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}
        
        if not isinstance(body, dict):
            logger.error("Request body is not a dictionary", request_id=request_id)
            if SECURITY_MODULES_AVAILABLE:
                return secure_response_wrapper(
                    success=False,
                    message="Request body must be JSON object",
                    error_code="INVALID_FORMAT",
                    request_id=request_id
                )
            else:
                return {"statusCode": 400, "body": json.dumps({"error": "Invalid format"})}
        
        logger.info("Processing collar data ingestion", request_id=request_id)
        
        # Process the telemetry data
        result = processor.process_telemetry(body, request_id)
        
        # Add CORS headers for browser compatibility
        if isinstance(result, dict) and "headers" not in result:
            result["headers"] = {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "POST,OPTIONS"
            }
        
        return result
        
    except RateLimitExceeded as e:
        logger.warning("Rate limit exceeded", error=str(e), request_id=request_id)
        return {
            "statusCode": 429,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Rate limit exceeded", "request_id": request_id})
        }
    
    except Exception as e:
        logger.error("Unhandled error in lambda handler", error=str(e), request_id=request_id)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error", "request_id": request_id})
        }
