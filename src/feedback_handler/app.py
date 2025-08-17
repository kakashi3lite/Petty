import json, os, logging, time
from typing import Any, Dict
from common.aws.s3 import put_json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FEEDBACK_BUCKET = os.getenv("FEEDBACK_BUCKET", "petty-feedback")

def _build_key(collar_id: str, event_id: str) -> str:
    return f"feedback/{collar_id}/{event_id}.json"

def lambda_handler(event, context):  # type: ignore
    """Persist user feedback for an event to S3 with SSE.

    Expected body: {"event_id": str, "collar_id": str, "user_feedback": "correct"|"incorrect", "segment": {...}?}
    """
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
        logger.info("stored feedback %s -> s3://%s/%s", event_id, FEEDBACK_BUCKET, key)
        return {"statusCode": 200, "body": json.dumps({"ok": True, "key": key})}
    except Exception as e:  # pragma: no cover
        logger.exception("feedback error")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
