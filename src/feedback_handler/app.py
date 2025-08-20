import json, os, logging, time
from typing import Any, Dict
from common.aws.s3 import put_json

# >>> PETTY:COPILOT:BEGIN:OBS-LOGGING
# Use powertools logger/tracer/metrics; read POWERTOOLS_SERVICE_NAME + POWERTOOLS_LOG_LEVEL
# Replace print() with logger.info/exception; add metrics.add_metric('Requests', 'Count', 1)
# Decorate handlers with @tracer.capture_lambda_handler
try:
    from aws_lambda_powertools import Logger, Tracer, Metrics
    from aws_lambda_powertools.utilities.typing import LambdaContext
    AWS_POWERTOOLS_AVAILABLE = True
    logger = Logger(service=os.getenv("POWERTOOLS_SERVICE_NAME", "feedback-handler"))
    tracer = Tracer(service=os.getenv("POWERTOOLS_SERVICE_NAME", "feedback-handler"))
    metrics = Metrics(service=os.getenv("POWERTOOLS_SERVICE_NAME", "feedback-handler"), namespace="Petty")
except ImportError:
    AWS_POWERTOOLS_AVAILABLE = False
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
# <<< PETTY:COPILOT:END:OBS-LOGGING

FEEDBACK_BUCKET = os.getenv("FEEDBACK_BUCKET", "petty-feedback")

def _build_key(collar_id: str, event_id: str) -> str:
    return f"feedback/{collar_id}/{event_id}.json"

@tracer.capture_lambda_handler if AWS_POWERTOOLS_AVAILABLE else lambda x: x
@logger.inject_lambda_context(log_event=True) if AWS_POWERTOOLS_AVAILABLE else lambda x: x
def lambda_handler(event, context):  # type: ignore
    """Persist user feedback for an event to S3 with SSE.

    Expected body: {"event_id": str, "collar_id": str, "user_feedback": "correct"|"incorrect", "segment": {...}?}
    """
    # Add metrics for request count
    if AWS_POWERTOOLS_AVAILABLE:
        metrics.add_metric(name="Requests", unit="Count", value=1)
    
    try:
        body_raw = event.get("body") if isinstance(event, dict) else None
        body: Dict[str, Any] = json.loads(body_raw or "{}")
        event_id = str(body.get("event_id") or "").strip()
        collar_id = str(body.get("collar_id") or "").strip()
        feedback = body.get("user_feedback")
        if not event_id or not collar_id or feedback not in ("correct", "incorrect"):
            return {"statusCode": 400, "body": json.dumps({"error": "invalid payload"})}

        # Optional raw segment if provided (placeholder for future retrieval logic)
        segment = body.get("segment")
        # Guard overly large segment ( > 64KB ) to avoid oversized objects
        if isinstance(segment, dict):
            seg_len = len(json.dumps(segment))
            if seg_len > 64 * 1024:
                return {"statusCode": 413, "body": json.dumps({"error": "segment too large"})}
        doc: Dict[str, Any] = {
            "event_id": event_id,
            "collar_id": collar_id,
            "user_feedback": feedback,
            "ts": int(time.time()),
        }
        if isinstance(segment, dict):
            doc["segment"] = segment

        key = _build_key(collar_id, event_id)
        
        # >>> PETTY:COPILOT:BEGIN:S3-PUTJSON
        # Use put_json(...); ContentType must be application/json
        # If FEEDBACK_KMS_KEY_ID env set, use SSE-KMS (ServerSideEncryption='aws:kms', SSEKMSKeyId=...)
        # Key format: feedback/{collar_id}/{event_id}.json
        kms_key_id = os.getenv("FEEDBACK_KMS_KEY_ID")
        put_json(FEEDBACK_BUCKET, key, doc, kms_key_id=kms_key_id, content_type="application/json")
        # <<< PETTY:COPILOT:END:S3-PUTJSON
        
        logger.info("stored feedback", extra={"event_id": event_id, "bucket": FEEDBACK_BUCKET, "key": key})
        return {"statusCode": 200, "body": json.dumps({"ok": True, "key": key})}
    except Exception as e:  # pragma: no cover
        logger.exception("feedback error")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
