import json, os, logging, time
from typing import Any, Dict
from common.aws.s3 import put_json

# >>> PETTY:COPILOT:BEGIN:OBS-LOGGING
# Use powertools logger/tracer/metrics; read POWERTOOLS_SERVICE_NAME + POWERTOOLS_LOG_LEVEL
# Replace print() with logger.info/exception; add metrics.add_metric('Requests', 'Count', 1)
# Decorate handlers with @tracer.capture_lambda_handler
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.observability.powertools import setup_powertools, add_request_metric

# Setup powertools with service name from environment
logger, tracer, metrics = setup_powertools("feedback-handler")
# <<< PETTY:COPILOT:END:OBS-LOGGING

FEEDBACK_BUCKET = os.getenv("FEEDBACK_BUCKET", "petty-feedback")

def _build_key(collar_id: str, event_id: str) -> str:
    return f"feedback/{collar_id}/{event_id}.json"

@tracer.capture_lambda_handler if tracer else lambda x: x
def lambda_handler(event, context):  # type: ignore
    """Persist user feedback for an event to S3 with SSE.

    Expected body: {"event_id": str, "collar_id": str, "user_feedback": "correct"|"incorrect", "segment": {...}?}
    """
    # Add request metric
    add_request_metric()
    
    event_id = ""
    collar_id = ""
    try:
        body_raw = event.get("body") if isinstance(event, dict) else None
        body: Dict[str, Any] = json.loads(body_raw or "{}")
        event_id = str(body.get("event_id") or "").strip()
        collar_id = str(body.get("collar_id") or "").strip()
        feedback = body.get("user_feedback")
        
        logger.info("Processing feedback", event_id=event_id, collar_id=collar_id, feedback=feedback)
        
        if not event_id or not collar_id or feedback not in ("correct", "incorrect"):
            logger.warning("Invalid feedback payload", event_id=event_id, collar_id=collar_id, feedback=feedback)
            return {"statusCode": 400, "body": json.dumps({"error": "invalid payload"})}

        # Optional raw segment if provided (placeholder for future retrieval logic)
        segment = body.get("segment")
        # Guard overly large segment ( > 64KB ) to avoid oversized objects
        if isinstance(segment, dict):
            seg_len = len(json.dumps(segment))
            if seg_len > 64 * 1024:
                logger.warning("Segment too large", event_id=event_id, size=seg_len)
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
        put_json(FEEDBACK_BUCKET, key, doc)
        logger.info("Feedback stored successfully", event_id=event_id, bucket=FEEDBACK_BUCKET, key=key)
        return {"statusCode": 200, "body": json.dumps({"ok": True, "key": key})}
    except Exception as e:  # pragma: no cover
        logger.exception("Feedback processing failed", event_id=event_id, collar_id=collar_id)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
