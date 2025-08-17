"""Tests for S3 put_json helper with KMS support and content-type validation."""
import json

import boto3
import pytest
from moto import mock_aws

from src.common.aws.s3 import put_json


@mock_aws
def test_put_json_default_sse_s3():
    """Test put_json with default SSE-S3 encryption (backward compatibility)."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    key = "test-key.json"
    payload = {"message": "hello", "count": 42}

    # Call without KMS key (should use SSE-S3)
    put_json(bucket, key, payload)

    # Verify object was stored with correct encryption
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ServerSideEncryption"] == "AES256"
    assert obj["ContentType"] == "application/json"

    # Verify JSON round-trip
    stored_data = json.loads(obj["Body"].read())
    assert stored_data == payload


@mock_aws
def test_put_json_with_kms_encryption():
    """Test put_json with SSE-KMS encryption."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    key = "test-key.json"
    payload = {"secure": "data", "timestamp": 1234567890}
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"

    # Call with KMS key
    put_json(bucket, key, payload, kms_key_id=kms_key_id)

    # Verify object was stored with KMS encryption
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ServerSideEncryption"] == "aws:kms"
    assert obj["SSEKMSKeyId"] == kms_key_id
    assert obj["ContentType"] == "application/json"

    # Verify JSON round-trip
    stored_data = json.loads(obj["Body"].read())
    assert stored_data == payload


@mock_aws
def test_put_json_content_type_validation():
    """Test that put_json enforces application/json content type."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    key = "test-key.json"
    payload = {"data": "test"}

    # Test with valid content type
    put_json(bucket, key, payload, content_type="application/json")

    # Verify it was stored
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ContentType"] == "application/json"

    # Test with invalid content types
    invalid_content_types = [
        "text/plain",
        "application/xml",
        "text/html",
        "application/octet-stream",
        "image/jpeg",
        "",
        "application/json; charset=utf-8"  # Even with charset is rejected for strict validation
    ]

    for content_type in invalid_content_types:
        with pytest.raises(ValueError, match=f"Invalid content_type '{content_type}'. Only 'application/json' is allowed."):
            put_json(bucket, key, payload, content_type=content_type)


@mock_aws
def test_put_json_kms_with_content_type():
    """Test put_json with both KMS encryption and explicit content type."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    key = "test-key.json"
    payload = {"secure": True, "data": [1, 2, 3]}
    kms_key_id = "alias/my-key"

    put_json(bucket, key, payload, kms_key_id=kms_key_id, content_type="application/json")

    # Verify both KMS and content type are set correctly
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ServerSideEncryption"] == "aws:kms"
    assert obj["SSEKMSKeyId"] == kms_key_id
    assert obj["ContentType"] == "application/json"

    # Verify JSON round-trip
    stored_data = json.loads(obj["Body"].read())
    assert stored_data == payload


@mock_aws
def test_put_json_complex_data_structures():
    """Test put_json handles complex JSON data structures correctly."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    key = "complex-data.json"
    complex_payload = {
        "nested": {
            "deeply": {
                "nested": "value"
            }
        },
        "array": [1, 2, {"inner": "object"}],
        "null_value": None,
        "boolean": True,
        "float": 3.14159,
        "unicode": "🐕 pet data"
    }

    put_json(bucket, key, complex_payload)

    # Verify round-trip preserves data structure
    obj = s3.get_object(Bucket=bucket, Key=key)
    stored_data = json.loads(obj["Body"].read())
    assert stored_data == complex_payload

    # Verify JSON is minified (no spaces after separators)
    obj = s3.get_object(Bucket=bucket, Key=key)  # Get fresh object
    body_str = obj["Body"].read().decode("utf-8")
    assert ", " not in body_str  # No spaces after commas
    assert ": " not in body_str  # No spaces after colons


@mock_aws
def test_put_json_keyword_only_parameters():
    """Test that kms_key_id and content_type are keyword-only parameters."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    key = "test-key.json"
    payload = {"test": "data"}

    # This should work (positional args for bucket, key, payload)
    put_json(bucket, key, payload)

    # This should fail - kms_key_id and content_type must be keyword-only
    with pytest.raises(TypeError):
        put_json(bucket, key, payload, "some-kms-key")  # type: ignore

    with pytest.raises(TypeError):
        put_json(bucket, key, payload, "some-kms-key", "application/json")  # type: ignore


@mock_aws
def test_put_json_backward_compatibility():
    """Test that existing calls to put_json continue to work unchanged."""
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    # This is how the existing feedback handler calls put_json
    key = "feedback/SN-123/evt-123.json"
    doc = {
        "event_id": "evt-123",
        "collar_id": "SN-123",
        "user_feedback": "correct",
        "ts": 1234567890,
    }

    # Should work exactly as before
    put_json(bucket, key, doc)

    # Verify behavior is unchanged
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ServerSideEncryption"] == "AES256"  # Default SSE-S3
    assert obj["ContentType"] == "application/json"

    stored_data = json.loads(obj["Body"].read())
    assert stored_data == doc
