"""
Production-grade feedback handler Lambda with security and observability
Handles user feedback on AI behavioral analysis with comprehensive validation
"""

import json
import os
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

# Import production modules
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
        verify_jwt_token
    )
    from common.security.secrets_manager import secrets_manager
    from common.security.redaction import safe_log, redact_pii
    PRODUCTION_MODULES_AVAILABLE = True
except ImportError as e:
    PRODUCTION_MODULES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.warning(f"Production modules not available - using fallbacks: {e}")

# Fallback S3 import
try:
    from common.aws.s3 import put_json
    S3_HELPER_AVAILABLE = True
except ImportError:
    S3_HELPER_AVAILABLE = False

# Environment configuration
FEEDBACK_BUCKET = os.getenv("FEEDBACK_BUCKET", "petty-feedback-data")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize AWS S3 client
session = boto3.Session()
s3_client = session.client(
    's3',
    region_name=AWS_REGION,
    config=boto3.session.Config(
        retries={'max_attempts': 3, 'mode': 'adaptive'},
        max_pool_connections=20
    )
)

class FeedbackHandler:
    """Production-grade feedback handler with comprehensive validation and security"""
    
    def __init__(self):
        self.logger = logger
        self.bucket_name = FEEDBACK_BUCKET
        
    def _validate_feedback_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize feedback payload
        
        Args:
            payload: Raw feedback payload
            
        Returns:
            Validated and sanitized payload
            
        Raises:
            ValueError: If payload is invalid
        """
        required_fields = ["event_id", "user_feedback"]
        
        # Check required fields
        for field in required_fields:
            if field not in payload or not payload[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate event_id format
        event_id = str(payload["event_id"]).strip()
        if not event_id or len(event_id) > 100:
            raise ValueError("Invalid event_id format")
        
        # Validate feedback content
        user_feedback = str(payload["user_feedback"]).strip()
        if len(user_feedback) > 1000:
            raise ValueError("Feedback text too long (max 1000 characters)")
        
        # Sanitize feedback content to prevent XSS
        user_feedback = redact_pii(user_feedback) if PRODUCTION_MODULES_AVAILABLE else user_feedback
        user_feedback = user_feedback.replace('<', '&lt;').replace('>', '&gt;')
        
        # Validate optional timestamp
        timestamp = payload.get("timestamp")
        if timestamp:
            try:
                # Validate ISO format timestamp
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValueError("Invalid timestamp format, use ISO 8601")
        
        # Validate optional segment data
        segment = payload.get("segment")
        if segment:
            if not isinstance(segment, dict):
                raise ValueError("Segment must be a JSON object")
            
            # Size limit check (64KB)
            segment_size = len(json.dumps(segment))
            if segment_size > 64 * 1024:
                raise ValueError("Segment data too large (max 64KB)")
        
        return {
            "event_id": event_id,
            "user_feedback": user_feedback,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "segment": segment
        }
    
    def _build_storage_key(self, event_id: str, feedback_id: str) -> str:
        """
        Build S3 storage key for feedback
        
        Args:
            event_id: Event identifier
            feedback_id: Unique feedback identifier
            
        Returns:
            S3 key for storage
        """
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        return f"feedback/{date_prefix}/{event_id}/{feedback_id}.json"
    
    @monitor_performance("feedback_storage")
    def store_feedback(self, validated_payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Store validated feedback to S3
        
        Args:
            validated_payload: Validated feedback data
            user_id: Authenticated user ID
            
        Returns:
            Storage result with metadata
        """
        start_time = time.time()
        feedback_id = str(uuid.uuid4())
        
        try:
            # Prepare feedback document
            feedback_doc = {
                "feedback_id": feedback_id,
                "event_id": validated_payload["event_id"],
                "user_feedback": validated_payload["user_feedback"],
                "timestamp": validated_payload["timestamp"],
                "user_id": user_id,
                "environment": ENVIRONMENT,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0"
            }
            
            # Add segment data if present
            if validated_payload.get("segment"):
                feedback_doc["segment"] = validated_payload["segment"]
            
            # Generate storage key
            storage_key = self._build_storage_key(validated_payload["event_id"], feedback_id)
            
            # Store to S3
            if S3_HELPER_AVAILABLE:
                # Use existing S3 helper
                put_json(self.bucket_name, storage_key, feedback_doc)
            else:
                # Direct S3 client usage
                s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=storage_key,
                    Body=json.dumps(feedback_doc),
                    ContentType='application/json',
                    ServerSideEncryption='AES256',
                    Metadata={
                        'environment': ENVIRONMENT,
                        'user_id': user_id or 'anonymous',
                        'created_by': 'petty-feedback-handler'
                    }
                )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Log business event
            if PRODUCTION_MODULES_AVAILABLE:
                obs_manager.log_business_event(
                    "user_feedback_stored",
                    event_id=validated_payload["event_id"],
                    feedback_id=feedback_id,
                    user_id=user_id,
                    storage_key=storage_key,
                    processing_time_ms=processing_time
                )
                
                # Add custom metrics
                metrics.add_metric(name="feedback_stored", unit="Count", value=1)
                metrics.add_metric(name="feedback_processing_duration", unit="Milliseconds", value=processing_time)
            
            self.logger.info(
                "Feedback stored successfully",
                extra={
                    "feedback_id": feedback_id,
                    "event_id": validated_payload["event_id"],
                    "user_id": user_id,
                    "storage_key": storage_key,
                    "bucket": self.bucket_name,
                    "processing_time_ms": processing_time
                }
            )
            
            return {
                "feedback_id": feedback_id,
                "storage_key": storage_key,
                "processing_time_ms": processing_time,
                "stored_at": datetime.now(timezone.utc).isoformat()
            }
            
        except (ClientError, BotoCoreError) as e:
            processing_time = (time.time() - start_time) * 1000
            
            if PRODUCTION_MODULES_AVAILABLE:
                obs_manager.log_security_event(
                    "feedback_storage_error",
                    "medium",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "event_id": validated_payload["event_id"],
                        "user_id": user_id,
                        "processing_time_ms": processing_time
                    }
                )
            
            self.logger.error(
                "Failed to store feedback to S3",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "event_id": validated_payload["event_id"],
                    "user_id": user_id,
                    "bucket": self.bucket_name,
                    "processing_time_ms": processing_time
                }
            )
            
            raise Exception(f"Failed to store feedback: {e}")

# Global feedback handler instance
feedback_handler = FeedbackHandler()

def authenticate_request(event: Dict[str, Any]) -> Optional[str]:
    """Authenticate API request and return user ID"""
    if not PRODUCTION_MODULES_AVAILABLE or ENVIRONMENT != "production":
        return None
    
    try:
        headers = event.get("headers", {})
        auth_header = headers.get("authorization") or headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        token_payload = production_token_manager.verify_token(token)
        
        return token_payload.user_id if token_payload else None
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        return None

@lambda_handler_with_observability
@log_api_request("POST", "/v1/submit-feedback")
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Production-grade Lambda handler for user feedback submission
    
    Features:
    - JWT token authentication (optional in development)
    - Input validation and sanitization
    - PII redaction and XSS prevention
    - Comprehensive error handling
    - S3 storage with encryption
    - Structured logging and observability
    - Performance monitoring
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
        
        # Authenticate request (optional in development)
        user_id = authenticate_request(event)
        
        # Parse request body
        body_raw = event.get("body")
        if not body_raw:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Request body is required",
                    "request_id": request_id
                })
            }
        
        try:
            body = json.loads(body_raw) if isinstance(body_raw, str) else body_raw
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in request body", extra={
                "error": str(e),
                "request_id": request_id
            })
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Invalid JSON format",
                    "request_id": request_id
                })
            }
        
        if not isinstance(body, dict):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Request body must be a JSON object",
                    "request_id": request_id
                })
            }
        
        logger.info("Processing feedback submission", extra={
            "request_id": request_id,
            "user_id": user_id,
            "event_id": body.get("event_id", "unknown")
        })
        
        # Validate and sanitize payload
        try:
            validated_payload = feedback_handler._validate_feedback_payload(body)
        except ValueError as e:
            logger.warning("Invalid feedback payload", extra={
                "error": str(e),
                "request_id": request_id,
                "user_id": user_id
            })
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": f"Validation error: {str(e)}",
                    "request_id": request_id
                })
            }
        
        # Store feedback
        try:
            storage_result = feedback_handler.store_feedback(validated_payload, user_id)
        except Exception as e:
            logger.error("Failed to store feedback", extra={
                "error": str(e),
                "request_id": request_id,
                "user_id": user_id
            })
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Failed to store feedback",
                    "request_id": request_id
                })
            }
        
        # Return success response
        response_body = {
            "success": True,
            "feedback_id": storage_result["feedback_id"],
            "message": "Feedback stored successfully",
            "request_id": request_id,
            "processing_time_ms": storage_result["processing_time_ms"]
        }
        
        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Correlation-ID",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block"
            },
            "body": json.dumps(response_body)
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error("Unhandled error in feedback handler", extra={
            "error": error_msg,
            "error_type": type(e).__name__,
            "request_id": request_id,
            "user_id": user_id if 'user_id' in locals() else None
        })
        
        if PRODUCTION_MODULES_AVAILABLE:
            obs_manager.log_security_event(
                "feedback_handler_error",
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
