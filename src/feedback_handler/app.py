import json

# >>> POWDTOOLS_REFACTOR_START >>>
from common.observability.powertools import MetricUnit, logger, metrics, tracer

# <<< POWDTOOLS_REFACTOR_END <<<

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    metrics.add_metric(name="Requests", unit=MetricUnit.Count, value=1)
    try:
        body = json.loads(event.get("body") or "{}")
        event_id = body.get("event_id")
        feedback = body.get("user_feedback")
        logger.append_keys(event_id=event_id)
        if not event_id or feedback not in ("correct","incorrect"):
            logger.info("invalid payload", event_id=event_id, feedback=feedback)
            return {"statusCode": 400, "body": json.dumps({"error":"invalid payload"})}
        # TODO: fetch raw segment for event_id (from Timestream), then write labeled JSON to S3
        logger.info("feedback received", event_id=event_id, feedback=feedback)
        return {"statusCode": 200, "body": json.dumps({"ok": True})}
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("feedback error", error=str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
