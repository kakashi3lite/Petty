"""Lightweight S3 helpers with server-side encryption (SSE-S3)."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

_S3 = None

def _client():
    global _S3
    if _S3 is None:
        _S3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    return _S3


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, max=2),
       retry=retry_if_exception_type(ClientError))
def put_json(bucket: str, key: str, payload: dict[str, Any], *, kms_key_id: str | None = None, content_type: str = "application/json") -> None:
    """Put a JSON document with SSE and minimal retries.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        payload: JSON-serializable data to store
        kms_key_id: Optional KMS key ID for SSE-KMS encryption. If provided,
                   uses SSE-KMS; otherwise uses SSE-S3 (AES256)
        content_type: Content type for the object. Must be "application/json"

    Raises:
        ValueError: If content_type is not "application/json"

    Retries only on AWS client errors. JSON is minified deterministically.
    """
    # Validate content type - only allow application/json for security
    if content_type != "application/json":
        raise ValueError(f"Invalid content_type '{content_type}'. Only 'application/json' is allowed.")

    body = json.dumps(payload, separators=(",", ":"))
    logging.getLogger(__name__).debug("put_json bucket=%s key=%s bytes=%d kms_key_id=%s",
                                    bucket, key, len(body), kms_key_id)

    # Build put_object parameters
    put_params = {
        "Bucket": bucket,
        "Key": key,
        "Body": body.encode("utf-8"),
        "ContentType": content_type,
    }

    # Configure server-side encryption
    if kms_key_id:
        # Use SSE-KMS with specified key
        put_params["ServerSideEncryption"] = "aws:kms"
        put_params["SSEKMSKeyId"] = kms_key_id
    else:
        # Use SSE-S3 (default AES256)
        put_params["ServerSideEncryption"] = "AES256"

    _client().put_object(**put_params)
