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

# Import security and observability modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# >>> POWDTOOLS_REFACTOR_START >>>
from common.observability.powertools import logger, tracer, metrics, MetricUnit  # centralized
try:
    from aws_lambda_powertools.utilities.typing import LambdaContext  # type: ignore
except ImportError:
    # Fallback when powertools not available
    class LambdaContext:
        aws_request_id: str = "unknown"
        function_name: str = "unknown"
        function_version: str = "unknown"
        invoked_function_arn: str = "unknown"
        memory_limit_in_mb: int = 128
        remaining_time_in_millis = lambda self: 30000
# <<< POWDTOOLS_REFACTOR_END <<<

# Import Timestream helper
from common.aws.timestream import write_records, build_collar_record

try:
    from common.security.input_validators import validate_collar_data, InputValidator
    from common.security.output_schemas import secure_response_wrapper
    from common.security.rate_limiter import rate_limit_decorator, RateLimitExceeded
    from common.observability.logger import get_logger
    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False
    logging.warning("Security modules not available - using fallbacks")

# Environment configuration
TIMESTREAM_DATABASE = os.getenv("TIMESTREAM_DATABASE", "PettyDB")
TIMESTREAM_TABLE = os.getenv("TIMESTREAM_TABLE", "CollarMetrics")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

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
                
        except ValueError as e:
            # Record validation failure metrics
            metrics.add_metric(name="ValidationErrors", unit=MetricUnit.Count, value=1)
            
            self.logger.warning(
                "Validation failed",
                error=str(e),
                request_id=request_id,
                collar_id=event_body.get("collar_id") if isinstance(event_body, dict) else "unknown"
            )
            
            if SECURITY_MODULES_AVAILABLE:
                return secure_response_wrapper(
                    success=False,
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    request_id=request_id
                )
            else:
                return {"statusCode": 400, "body": json.dumps({"error": str(e), "details": "Validation failed"})}
                
        except Exception as e:
            # Record failure metrics
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
                return {"statusCode": 500, "body": json.dumps({"error": "Internal server error"})}
    
    def _fallback_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback validation when security modules unavailable.
        Validates: collar_id, ISO8601 timestamp, int heart_rate, enum activity_level, GeoJSON Point
        """
        required_fields = ["collar_id", "timestamp", "heart_rate", "activity_level", "location"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate collar_id (string)
        collar_id = data["collar_id"]
        if not isinstance(collar_id, str) or not collar_id.strip():
            raise ValueError("collar_id must be a non-empty string")
        
        # Validate timestamp (ISO8601 format)
        timestamp = data["timestamp"]
        if not isinstance(timestamp, str):
            raise ValueError("timestamp must be an ISO8601 string")
        try:
            # Try parsing as ISO8601
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("timestamp must be in ISO8601 format")
        
        # Validate heart_rate (integer, reasonable range)
        hr = data["heart_rate"]
        if not isinstance(hr, int) or not (30 <= hr <= 300):
            raise ValueError(f"heart_rate must be an integer between 30 and 300, got: {hr}")
        
        # Validate activity_level (enum: 0, 1, 2)
        activity = data["activity_level"]
        if not isinstance(activity, int) or activity not in [0, 1, 2]:
            raise ValueError(f"activity_level must be 0, 1, or 2, got: {activity}")
        
        # Validate location (GeoJSON Point)
        location = data["location"]
        if not isinstance(location, dict):
            raise ValueError("location must be a GeoJSON Point object")
        
        if location.get("type") != "Point":
            raise ValueError("location type must be 'Point'")
        
        coordinates = location.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            raise ValueError("location coordinates must be [longitude, latitude] array")
        
        longitude, latitude = coordinates
        if not isinstance(longitude, (int, float)) or not isinstance(latitude, (int, float)):
            raise ValueError("coordinates must be numeric values")
        
        if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
            raise ValueError("coordinates out of valid range")
        
        return data
    
    def _write_to_timestream(self, data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Write validated data to AWS Timestream using helper module.
        
        Args:
            data: Validated collar data
            request_id: Request identifier for tracing
            
        Returns:
            Timestream write response
        """
        try:
            # Build Timestream record using helper
            record = build_collar_record(
                collar_id=data["collar_id"],
                timestamp=data["timestamp"],
                heart_rate=data["heart_rate"],
                activity_level=data["activity_level"],
                location=data["location"],
                environment=ENVIRONMENT
            )
            
            # Write to Timestream using helper with retry logic
            response = write_records(
                database=TIMESTREAM_DATABASE,
                table=TIMESTREAM_TABLE,
                records=[record],
                region_name=AWS_REGION
            )
            
            self.logger.debug(
                "Data written to Timestream",
                database=TIMESTREAM_DATABASE,
                table=TIMESTREAM_TABLE,
                collar_id=data["collar_id"],
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
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

@tracer.capture_lambda_handler  # tracing
@logger.inject_lambda_context(log_event=True)  # structured logs with event
@rate_limit_decorator("ingest", tokens=1, key_func=lambda event, context: (event.get("body", {}) or {}).get("collar_id", "unknown")) if SECURITY_MODULES_AVAILABLE else (lambda f: f)
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
    metrics.add_metric(name="Requests", unit=MetricUnit.Count, value=1)

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
                    return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON", "details": "Request body must be valid JSON"})}
        
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
                return {"statusCode": 400, "body": json.dumps({"error": "Invalid format", "details": "Request body must be JSON object"})}
        
        logger.append_keys(collar_id=body.get("collar_id"))
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
        
    except RateLimitExceeded as e:  # type: ignore
        logger.warning("Rate limit exceeded", error=str(e), request_id=request_id)
        return {
            "statusCode": 429,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Rate limit exceeded", "request_id": request_id})
        }
    
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Unhandled error in lambda handler", error=str(e), request_id=request_id)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error", "request_id": request_id})
        }
