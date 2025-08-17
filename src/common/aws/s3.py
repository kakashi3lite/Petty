"""Lightweight S3 helpers with server-side encryption (SSE-S3/KMS) and content validation."""
from __future__ import annotations
import json
import os
import mimetypes
from typing import Any, Dict, Optional, Union
import boto3
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

_S3 = None

# Security hardening: strict content type whitelist
ALLOWED_CONTENT_TYPES = {
    'application/json',
    'text/plain',
    'text/csv',
    'application/csv',
    'text/tab-separated-values',
    'application/octet-stream',  # For binary telemetry data
}

def _client():
    global _S3
    if _S3 is None:
        _S3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    return _S3


def _get_encryption_config() -> Dict[str, str]:
    """Get encryption configuration based on environment variables."""
    kms_key_id = os.getenv("PETTY_KMS_KEY_ID")
    
    if kms_key_id:
        return {
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": kms_key_id
        }
    else:
        return {
            "ServerSideEncryption": "AES256"
        }


def _validate_content_type(content_type: str) -> None:
    """Validate content type against security whitelist."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Content type '{content_type}' not allowed. "
            f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
        )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, max=2),
       retry=retry_if_exception_type(ClientError))
def put_json(bucket: str, key: str, data: Dict[str, Any]) -> None:
    """Put a JSON document with configurable encryption and strict validation.

    Uses KMS encryption if PETTY_KMS_KEY_ID environment variable is set,
    otherwise falls back to SSE-S3. JSON is minified deterministically.
    """
    content_type = "application/json"
    _validate_content_type(content_type)
    
    body = json.dumps(data, separators=(",", ":"))
    logging.getLogger(__name__).debug("put_json bucket=%s key=%s bytes=%d", bucket, key, len(body))
    
    put_params = {
        "Bucket": bucket,
        "Key": key,
        "Body": body.encode("utf-8"),
        "ContentType": content_type,
        **_get_encryption_config()
    }
    
    _client().put_object(**put_params)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, max=2),
       retry=retry_if_exception_type(ClientError))
def put_text(bucket: str, key: str, content: str, content_type: str = "text/plain") -> None:
    """Put text content with encryption and content type validation."""
    _validate_content_type(content_type)
    
    logging.getLogger(__name__).debug("put_text bucket=%s key=%s bytes=%d", bucket, key, len(content))
    
    put_params = {
        "Bucket": bucket,
        "Key": key,
        "Body": content.encode("utf-8"),
        "ContentType": content_type,
        **_get_encryption_config()
    }
    
    _client().put_object(**put_params)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, max=2),
       retry=retry_if_exception_type(ClientError))
def put_binary(bucket: str, key: str, data: bytes, content_type: Optional[str] = None) -> None:
    """Put binary data with encryption and content type validation.
    
    If content_type is not provided, it will be guessed from the key extension.
    """
    if content_type is None:
        content_type, _ = mimetypes.guess_type(key)
        if content_type is None:
            content_type = "application/octet-stream"
    
    _validate_content_type(content_type)
    
    logging.getLogger(__name__).debug("put_binary bucket=%s key=%s bytes=%d", bucket, key, len(data))
    
    put_params = {
        "Bucket": bucket,
        "Key": key,
        "Body": data,
        "ContentType": content_type,
        **_get_encryption_config()
    }
    
    _client().put_object(**put_params)


def get_encryption_status(bucket: str, key: str) -> Dict[str, Any]:
    """Get encryption status and metadata for an S3 object."""
    try:
        response = _client().head_object(Bucket=bucket, Key=key)
        return {
            "server_side_encryption": response.get("ServerSideEncryption"),
            "kms_key_id": response.get("SSEKMSKeyId"),
            "content_type": response.get("ContentType"),
            "last_modified": response.get("LastModified"),
            "etag": response.get("ETag")
        }
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            raise FileNotFoundError(f"Object s3://{bucket}/{key} not found")
        raise
