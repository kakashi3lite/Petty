"""Lightweight S3 helpers with server-side encryption (SSE-S3)."""
from __future__ import annotations
import json
import os
from typing import Any, Dict
import boto3

_S3 = None

def _client():
    global _S3
    if _S3 is None:
        _S3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    return _S3


def put_json(bucket: str, key: str, data: Dict[str, Any]) -> None:
    body = json.dumps(data, separators=(",", ":"))  # deterministic minified
    _client().put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
