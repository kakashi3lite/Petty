"""Lightweight S3 helpers with server-side encryption (SSE-S3)."""
from __future__ import annotations
import json
import os
from typing import Any, Dict
import boto3
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

_S3 = None

def _client():
    global _S3
    if _S3 is None:
        _S3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    return _S3


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, max=2),
       retry=retry_if_exception_type(ClientError))
def put_json(bucket: str, key: str, payload: Dict[str, Any], *, kms_key_id: str = None, content_type: str = "application/json") -> None:
    """Put a JSON document with SSE-S3 or SSE-KMS and minimal retries.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        payload: JSON serializable data
        kms_key_id: Optional KMS key ID for SSE-KMS encryption
        content_type: Content-Type header (defaults to application/json)

    Retries only on AWS client errors. JSON is minified deterministically.
    """
    body = json.dumps(payload, separators=(",", ":"))
    logging.getLogger(__name__).debug("put_json bucket=%s key=%s bytes=%d", bucket, key, len(body))
    
    # Build put_object parameters
    put_params = {
        "Bucket": bucket,
        "Key": key,
        "Body": body.encode("utf-8"),
        "ContentType": content_type,
    }
    
    # Add encryption parameters
    if kms_key_id:
        put_params["ServerSideEncryption"] = "aws:kms"
        put_params["SSEKMSKeyId"] = kms_key_id
    else:
        put_params["ServerSideEncryption"] = "AES256"
    
    _client().put_object(**put_params)
