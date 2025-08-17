import json
import os
from typing import Dict, Any
from moto import mock_aws
import boto3
from src.feedback_handler import app as feedback_app

@mock_aws
def test_feedback_persist_s3(monkeypatch):
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "petty-feedback"
    s3.create_bucket(Bucket=bucket)
    monkeypatch.setenv("FEEDBACK_BUCKET", bucket)

    event = {
        "body": json.dumps({
            "event_id": "evt-123",
            "collar_id": "SN-123",
            "user_feedback": "correct",
            "segment": {"raw": 1},
        })
    }

    resp = feedback_app.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])  # type: ignore
    key = body["key"]
    assert key == "feedback/SN-123/evt-123.json"

    obj = s3.get_object(Bucket=bucket, Key=key)
    # SSE-S3 sets header 'ServerSideEncryption' to 'AES256'
    assert obj["ServerSideEncryption"] == "AES256"
    payload = json.loads(obj["Body"].read())
    assert payload["user_feedback"] == "correct"
    assert payload["segment"] == {"raw": 1}
