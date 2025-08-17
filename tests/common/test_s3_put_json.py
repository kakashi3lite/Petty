"""Tests for S3 put_json helper with both SSE-S3 and SSE-KMS encryption."""
import json
import os
from typing import Dict, Any
from moto import mock_aws
import boto3
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "src"))

from common.aws.s3 import put_json


@mock_aws
def test_put_json_sse_s3_default():
    """Test put_json with default SSE-S3 encryption (existing behavior)."""
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)
    
    # Test data
    test_data = {
        "event_id": "test-123",
        "collar_id": "SN-456",
        "user_feedback": "correct",
        "timestamp": 1642723200
    }
    key = "test/object.json"
    
    # Call put_json without KMS key (should use SSE-S3)
    put_json(bucket, key, test_data)
    
    # Verify object was stored with correct encryption
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ServerSideEncryption"] == "AES256"
    assert obj["ContentType"] == "application/json"
    
    # Verify content
    stored_data = json.loads(obj["Body"].read())
    assert stored_data == test_data


@mock_aws 
def test_put_json_sse_kms():
    """Test put_json with SSE-KMS encryption."""
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)
    
    # Test data
    test_data = {
        "event_id": "test-456", 
        "collar_id": "SN-789",
        "user_feedback": "incorrect",
        "timestamp": 1642723300
    }
    key = "test/kms-object.json"
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    
    # Call put_json with KMS key
    put_json(bucket, key, test_data, kms_key_id=kms_key_id)
    
    # Verify object was stored with KMS encryption
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ServerSideEncryption"] == "aws:kms"
    assert obj["SSEKMSKeyId"] == kms_key_id
    assert obj["ContentType"] == "application/json"
    
    # Verify content
    stored_data = json.loads(obj["Body"].read())
    assert stored_data == test_data


@mock_aws
def test_put_json_custom_content_type():
    """Test put_json with custom content type."""
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)
    
    test_data = {"test": "data"}
    key = "test/custom-content.json"
    custom_content_type = "application/json; charset=utf-8"
    
    # Call put_json with custom content type
    put_json(bucket, key, test_data, content_type=custom_content_type)
    
    # Verify content type
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ContentType"] == custom_content_type
    assert obj["ServerSideEncryption"] == "AES256"  # Default SSE-S3


@mock_aws
def test_put_json_kms_with_custom_content_type():
    """Test put_json with both KMS encryption and custom content type."""
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)
    
    test_data = {"complex": {"nested": "data"}, "list": [1, 2, 3]}
    key = "test/kms-custom.json"
    kms_key_id = "alias/my-test-key"
    custom_content_type = "application/json; charset=utf-8"
    
    # Call put_json with both KMS and custom content type
    put_json(bucket, key, test_data, kms_key_id=kms_key_id, content_type=custom_content_type)
    
    # Verify all parameters
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ServerSideEncryption"] == "aws:kms"
    assert obj["SSEKMSKeyId"] == kms_key_id
    assert obj["ContentType"] == custom_content_type
    
    # Verify content
    stored_data = json.loads(obj["Body"].read())
    assert stored_data == test_data


@mock_aws
def test_put_json_enforces_application_json_default():
    """Test that put_json enforces application/json as default content type."""
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)
    
    test_data = {"strict": "content-type"}
    key = "test/strict-content-type.json"
    
    # Call put_json without specifying content_type
    put_json(bucket, key, test_data)
    
    # Verify default content type is application/json
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["ContentType"] == "application/json"


@mock_aws
def test_put_json_json_minification():
    """Test that JSON is properly minified (deterministic serialization)."""
    # Setup mock S3
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)
    
    # Test data with formatting that should be minified
    test_data = {
        "key_with_spaces": "value",
        "nested": {
            "array": [1, 2, 3],
            "boolean": True
        }
    }
    key = "test/minified.json"
    
    put_json(bucket, key, test_data)
    
    # Verify JSON is minified (no extra spaces)
    obj = s3.get_object(Bucket=bucket, Key=key)
    stored_json = obj["Body"].read().decode("utf-8")
    
    # Should be compact JSON without spaces after separators
    expected_json = json.dumps(test_data, separators=(",", ":"))
    assert stored_json == expected_json
    assert " " not in stored_json.replace(" ", "X")  # No spaces around separators


def test_put_json_backward_compatibility():
    """Test that the function maintains backward compatibility with positional arguments."""
    from common.aws.s3 import put_json
    import inspect
    
    # Check function signature allows positional arguments for first 3 params
    sig = inspect.signature(put_json)
    params = list(sig.parameters.values())
    
    # First three parameters should be positional
    assert params[0].name == "bucket"
    assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params[1].name == "key" 
    assert params[1].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params[2].name == "payload"
    assert params[2].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    
    # kms_key_id and content_type should be keyword-only
    assert params[3].name == "kms_key_id"
    assert params[3].kind == inspect.Parameter.KEYWORD_ONLY
    assert params[4].name == "content_type"
    assert params[4].kind == inspect.Parameter.KEYWORD_ONLY


if __name__ == "__main__":
    # Simple test runner for manual execution
    test_functions = [
        test_put_json_sse_s3_default,
        test_put_json_sse_kms,
        test_put_json_custom_content_type,
        test_put_json_kms_with_custom_content_type,
        test_put_json_enforces_application_json_default,
        test_put_json_json_minification,
        test_put_json_backward_compatibility,
    ]
    
    print("Running S3 put_json tests...")
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
        except Exception as e:
            print(f"❌ {test_func.__name__}: {e}")
    
    print("All tests completed!")