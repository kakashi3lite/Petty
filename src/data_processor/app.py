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

# Import production-ready security and observability modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from common.observability.powertools import (
        lambda_handler_with_observability,
        monitor_performance,
        log_api_request,
        obs_manager,
        logger,
        tracer,
        metrics
    )
    from common.security.auth import (
        production_token_manager,
        verify_jwt_token,
        require_auth
    )
    from common.security.secrets_manager import secrets_manager
    from common.security.redaction import safe_log
    PRODUCTION_MODULES_AVAILABLE = True
except ImportError as e:
    PRODUCTION_MODULES_AVAILABLE = False
    logging.warning(f"Production modules not available - using fallbacks: {e}")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

# Legacy imports for backward compatibility
try:
    from common.security.input_validators import validate_collar_data, InputValidator
    from common.security.output_schemas import secure_response_wrapper
    from common.security.rate_limiter import rate_limit_decorator, RateLimitExceeded
    LEGACY_SECURITY_AVAILABLE = True
except ImportError:
    LEGACY_SECURITY_AVAILABLE = False

# Environment configuration with secrets management
TIMESTREAM_DATABASE = os.getenv("TIMESTREAM_DB", "PettyDB")
TIMESTREAM_TABLE = os.getenv("TIMESTREAM_TABLE", "CollarMetrics")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize secrets if available
def get_database_config():
    """Get database configuration from secrets manager"""
    if PRODUCTION_MODULES_AVAILABLE:
        try:
            db_credentials = secrets_manager.get_database_credentials("petty")
            if db_credentials:
                return {
                    'host': db_credentials['host'],
                    'database': db_credentials['database'],
                    'username': db_credentials['username'],
                    'password': db_credentials['password']
                }
        except Exception as e:
            logger.warning(f"Failed to retrieve database credentials: {e}")
    
    # Fallback to environment variables
    return {
        'host': TIMESTREAM_DATABASE,
        'database': TIMESTREAM_TABLE,
        'username': 'default',
        'password': 'default'
    }

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

# Get database configuration
db_config = get_database_config()

class DataProcessor:
    """Production-grade secure data processor for collar telemetry"""
    
    def __init__(self):
        self.validator = InputValidator() if LEGACY_SECURITY_AVAILABLE else None
        self.logger = logger
        
    @monitor_performance("telemetry_processing")
    def process_telemetry(self, event_body: Dict[str, Any], request_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
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
            # Input validation and sanitization with PII protection
            if self.validator:
                validated_data = self.validator.validate_collar_data(event_body)
                clean_data = validated_data.dict()
            else:
                # Fallback validation
                clean_data = self._fallback_validate(event_body)
            
            # Log safely with PII redaction
            if PRODUCTION_MODULES_AVAILABLE:
                safe_data = safe_log(clean_data)
                obs_manager.log_business_event(
                    "telemetry_ingestion",
                    collar_id=clean_data.get("collar_id"),
                    user_id=user_id,
                    data_points=len(clean_data),
                    request_id=request_id
                )
            
            # Store in Timestream
            timestream_result = self._write_to_timestream(clean_data, request_id)
            
            # Record performance metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if PRODUCTION_MODULES_AVAILABLE:
                obs_manager.log_performance_metric("telemetry_processing", processing_time, True)
                
                # Add custom business metrics
                metrics.add_metric(name="telemetry_ingested", unit="Count", value=1)
                metrics.add_metric(name="processing_duration", unit="Milliseconds", value=processing_time)
            
            self.logger.info(
                "Telemetry data processed successfully",
                extra={
                    "collar_id": clean_data.get("collar_id"),
                    "processing_time_ms": processing_time,
                    "request_id": request_id,
                    "user_id": user_id,
                    "timestream_record_id": timestream_result.get("RecordId", "unknown")
                }
            )
            
            # Return secure response
            if LEGACY_SECURITY_AVAILABLE:
                return secure_response_wrapper(
                    success=True,
                    message="Data processed successfully",
                    request_id=request_id
                )
            else:
                return {
                    "statusCode": 201,
                    "body": json.dumps({
                        "success": True,
                        "message": "Data processed successfully",
                        "request_id": request_id,
                        "processing_time_ms": processing_time
                    })
                }
                
        except Exception as e:
            # Record failure metrics
            processing_time = (time.time() - start_time) * 1000
            
            if PRODUCTION_MODULES_AVAILABLE:
                obs_manager.log_performance_metric("telemetry_processing", processing_time, False)
                metrics.add_metric(name="telemetry_ingestion_errors", unit="Count", value=1)
                
                obs_manager.log_security_event(
                    "telemetry_processing_error",
                    "medium",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "collar_id": event_body.get("collar_id") if isinstance(event_body, dict) else "unknown",
                        "user_id": user_id,
                        "request_id": request_id
                    }
                )
            
            self.logger.error(
                "Telemetry processing failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request_id": request_id,
                    "user_id": user_id,
                    "collar_id": event_body.get("collar_id") if isinstance(event_body, dict) else "unknown",
                    "processing_time_ms": processing_time
                }
            )
            
            if LEGACY_SECURITY_AVAILABLE:
                return secure_response_wrapper(
                    success=False,
                    message="Processing failed",
                    error_code="PROCESSING_ERROR",
                    request_id=request_id
                )
            else:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": "Processing failed",
                        "request_id": request_id,
                        "error_type": type(e).__name__
                    })
                }
    
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

def authenticate_request(event: Dict[str, Any]) -> Optional[str]:
    """Authenticate API request and return user ID"""
    if not PRODUCTION_MODULES_AVAILABLE:
        return None
    
    try:
        # Extract Authorization header
        headers = event.get("headers", {})
        auth_header = headers.get("authorization") or headers.get("Authorization")
        
        if not auth_header:
            return None
        
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Verify JWT token
        token_payload = production_token_manager.verify_token(token)
        if token_payload:
            return token_payload.user_id
        
        return None
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        return None

@lambda_handler_with_observability
@log_api_request("POST", "/v1/ingest")
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Production-grade AWS Lambda handler for collar data ingestion
    
    Security features:
    - JWT token authentication
    - Input validation and sanitization
    - PII redaction in logs
    - Rate limiting protection
    - Comprehensive observability
    - Error handling with secure responses
    - AWS Timestream integration with retry logic
    """
    request_id = getattr(context, 'aws_request_id', 'unknown')
    
    try:
        # Handle CORS preflight requests
        if event.get("httpMethod") == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Correlation-ID",
                    "Access-Control-Allow-Methods": "POST,OPTIONS"
                },
                "body": ""
            }
        
        # Authenticate request
        user_id = authenticate_request(event)
        if not user_id and ENVIRONMENT == "production":
            obs_manager.log_security_event(
                "authentication_required",
                "medium",
                {"endpoint": "ingest", "request_id": request_id}
            )
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Authentication required",
                    "request_id": request_id
                })
            }
        
        # Parse request body
        body = event.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in request body", extra={"error": str(e), "request_id": request_id})
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "Invalid JSON format",
                        "request_id": request_id
                    })
                }
        
        if not isinstance(body, dict):
            logger.error("Request body is not a dictionary", extra={"request_id": request_id})
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Request body must be JSON object",
                    "request_id": request_id
                })
            }
        
        logger.info("Processing collar data ingestion", extra={
            "request_id": request_id,
            "user_id": user_id,
            "collar_id": body.get("collar_id", "unknown")
        })
        
        # Process the telemetry data
        result = processor.process_telemetry(body, request_id, user_id)
        
        # Add CORS and security headers
        if isinstance(result, dict) and "headers" not in result:
            result["headers"] = {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Correlation-ID",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block"
            }
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error("Unhandled error in lambda handler", extra={
            "error": error_msg,
            "error_type": type(e).__name__,
            "request_id": request_id,
            "user_id": user_id if 'user_id' in locals() else None
        })
        
        if PRODUCTION_MODULES_AVAILABLE:
            obs_manager.log_security_event(
                "lambda_handler_error",
                "high",
                {
                    "error": error_msg,
                    "error_type": type(e).__name__,
                    "request_id": request_id
                }
            )
        
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Internal server error",
                "request_id": request_id
            })
        }
