import json
import os
import time
import datetime
import random
from typing import Any

# >>> POWDTOOLS_REFACTOR_START >>>
from common.observability.powertools import MetricUnit, logger, metrics, tracer
# <<< POWDTOOLS_REFACTOR_END <<<
from common.aws.s3 import put_json

# Environment configuration
FEEDBACK_BUCKET = os.getenv("FEEDBACK_BUCKET", "petty-feedback-dev")

# Constants
MIN_EVENT_ID_PARTS = 3


def _extract_collar_id_from_event_id(event_id: str) -> str | None:
    """
    Extract collar_id from event_id.
    Event IDs are expected to have format like: evt_{collar_id}_{timestamp}
    If not in expected format, return None to let caller handle it.
    """
    try:
        if event_id.startswith("evt_"):
            parts = event_id.split("_")
            if len(parts) >= MIN_EVENT_ID_PARTS:
                return "_".join(parts[1:-1])  # Everything between evt_ and timestamp
    except Exception:
        # Log exception would be ideal but keeping minimal for now
        pass
    return None


def _simulate_raw_segment(event_id: str, collar_id: str) -> dict[str, Any]:
    """
    Simulate fetching raw segment data for the event_id.
    In production, this would query Timestream for the actual data.
    """
    # Generate simulated data similar to timeline generator
    base_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(0, 1440))  # noqa: S311
    ts = base_time.replace(microsecond=0).isoformat() + "Z"

    activity_level = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]  # noqa: S311
    heart_rate = 60 + (0 if activity_level == 0 else 20 if activity_level == 1 else 50) + random.randint(-5, 5)  # noqa: S311

    # Simulate NYC coordinates with small variations
    lon = -74.0060 + random.uniform(-0.001, 0.001)  # noqa: S311
    lat = 40.7128 + random.uniform(-0.001, 0.001)  # noqa: S311

    return {
        "collar_id": collar_id,
        "timestamp": ts,
        "heart_rate": heart_rate,
        "activity_level": activity_level,
        "location": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "event_id": event_id
    }

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):  # noqa: ARG001
    metrics.add_metric(name="Requests", unit=MetricUnit.Count, value=1)
    try:
        body = json.loads(event.get("body") or "{}")
        event_id = body.get("event_id")
        feedback = body.get("user_feedback")
        collar_id = body.get("collar_id")  # Allow collar_id to be provided explicitly

        logger.append_keys(event_id=event_id)

        # Validate required fields
        if not event_id or feedback not in ("correct", "incorrect"):
            logger.info("invalid payload", event_id=event_id, feedback=feedback)
            return {"statusCode": 400, "body": json.dumps({"error": "invalid payload"})}

        # Extract collar_id if not provided
        if not collar_id:
            collar_id = _extract_collar_id_from_event_id(event_id)
            if not collar_id:
                logger.error("could not extract collar_id from event_id", event_id=event_id)
                return {"statusCode": 400, "body": json.dumps({"error": "collar_id required or cannot be extracted from event_id"})}

        logger.append_keys(collar_id=collar_id)

        # Fetch raw segment data for the event (simulated for now)
        try:
            raw_segment = _simulate_raw_segment(event_id, collar_id)
            logger.info("fetched raw segment", segment_timestamp=raw_segment.get("timestamp"))
        except Exception as e:
            logger.error("failed to fetch raw segment", error=str(e))
            raw_segment = None

        # Build labeled feedback data
        labeled_data = {
            "event_id": event_id,
            "collar_id": collar_id,
            "user_feedback": feedback,
            "labeled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "raw_segment": raw_segment
        }

        # Build deterministic S3 key: feedback/{collar_id}/{event_id}.json
        s3_key = f"feedback/{collar_id}/{event_id}.json"

        # Store labeled feedback to S3 with SSE
        try:
            s3_response = put_json(
                bucket=FEEDBACK_BUCKET,
                key=s3_key,
                data=labeled_data,
                metadata={
                    "feedback-type": feedback,
                    "collar-id": collar_id,
                    "event-id": event_id
                }
            )

            metrics.add_metric(name="FeedbackStored", unit=MetricUnit.Count, value=1)
            logger.info(
                "feedback stored to S3",
                s3_bucket=FEEDBACK_BUCKET,
                s3_key=s3_key,
                etag=s3_response.get('ETag')
            )

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "ok": True,
                    "s3_key": s3_key,
                    "etag": s3_response.get('ETag')
                })
            }

        except Exception as e:
            metrics.add_metric(name="FeedbackStoreFailed", unit=MetricUnit.Count, value=1)
            logger.error("failed to store feedback to S3", error=str(e), s3_key=s3_key)
            return {"statusCode": 500, "body": json.dumps({"error": "failed to store feedback"})}

    except json.JSONDecodeError as e:
        logger.error("invalid JSON in request body", error=str(e))
        return {"statusCode": 400, "body": json.dumps({"error": "invalid JSON"})}
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("feedback error", error=str(e))
        metrics.add_metric(name="FeedbackError", unit=MetricUnit.Count, value=1)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
