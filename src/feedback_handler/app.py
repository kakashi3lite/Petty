import json, os, logging, time
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        event_id = body.get("event_id")
        feedback = body.get("user_feedback")
        if not event_id or feedback not in ("correct","incorrect"):
            return {"statusCode": 400, "body": json.dumps({"error":"invalid payload"})}
        # TODO: fetch raw segment for event_id (from Timestream), then write labeled JSON to S3
        logger.info("feedback: %s => %s", event_id, feedback)
        return {"statusCode": 200, "body": json.dumps({"ok": True})}
    except Exception as e:
        logger.exception("feedback error")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
