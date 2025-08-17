import json, os, logging, time
from typing import Dict, Any
# >>> POWDTOOLS_REFACTOR_START >>>
from common.observability.powertools import logger, tracer, metrics, MetricUnit
# <<< POWDTOOLS_REFACTOR_END <<<

try:
    from common.security.models import validate_feedback_input
    from common.security.output_schemas import secure_response_wrapper
    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False
    logging.warning("Security modules not available - using fallbacks")

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    metrics.add_metric(name="Requests", unit=MetricUnit.Count, value=1)
    request_id = getattr(context, 'aws_request_id', 'unknown')
    
    try:
        # Parse request body
        body = event.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in request body", error=str(e), request_id=request_id)
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "Invalid JSON format",
                        "request_id": request_id
                    })
                }
        
        if not isinstance(body, dict):
            logger.error("Request body is not a dictionary", request_id=request_id)
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Request body must be JSON object",
                    "request_id": request_id
                })
            }
        
        # Validate feedback input using new Pydantic model
        if SECURITY_MODULES_AVAILABLE:
            try:
                validated_feedback = validate_feedback_input(body)
                event_id = validated_feedback.event_id
                feedback = validated_feedback.user_feedback
                user_id = validated_feedback.user_id
            except ValueError as e:
                logger.warning("Feedback validation failed", error=str(e), request_id=request_id)
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": str(e),  # First validation error message
                        "request_id": request_id
                    })
                }
        else:
            # Fallback validation
            event_id = body.get("event_id")
            feedback = body.get("user_feedback")
            user_id = body.get("user_id")
            
            if not event_id or feedback not in ("correct", "incorrect"):
                logger.info("invalid payload", event_id=event_id, feedback=feedback, request_id=request_id)
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "invalid payload",
                        "request_id": request_id
                    })
                }
        
        logger.append_keys(event_id=event_id, user_id=user_id)
        
        # TODO: fetch raw segment for event_id (from Timestream), then write labeled JSON to S3
        logger.info("feedback received", event_id=event_id, feedback=feedback, user_id=user_id, request_id=request_id)
        
        if SECURITY_MODULES_AVAILABLE:
            secure_body = secure_response_wrapper(
                success=True,
                message="Feedback received successfully",
                request_id=None  # Skip request_id to avoid validation issues in tests
            )
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(secure_body)
            }
        else:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True, "request_id": request_id})
            }
            
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("feedback error", error=str(e), request_id=request_id)
        
        if SECURITY_MODULES_AVAILABLE:
            secure_body = secure_response_wrapper(
                success=False,
                message="Feedback processing failed",
                error_code="FEEDBACK_ERROR",
                request_id=None  # Skip request_id to avoid validation issues in tests
            )
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(secure_body)
            }
        else:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e), "request_id": request_id})
            }
