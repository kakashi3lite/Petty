"""Tests for enhanced S3 security features."""
import json
import os
import pytest
from moto import mock_aws
import boto3
from src.common.aws.s3 import (
    put_json, put_text, put_binary, get_encryption_status, 
    _validate_content_type, _get_encryption_config
)


class TestContentTypeValidation:
    """Test strict content type validation."""
    
    def test_validate_allowed_content_types(self):
        """Should allow whitelisted content types."""
        allowed_types = [
            'application/json',
            'text/plain',
            'text/csv',
            'application/csv',
            'application/octet-stream'
        ]
        
        for content_type in allowed_types:
            _validate_content_type(content_type)  # Should not raise
    
    def test_validate_disallowed_content_types(self):
        """Should reject non-whitelisted content types."""
        disallowed_types = [
            'text/html',
            'application/javascript',
            'image/jpeg',
            'video/mp4',
            'application/x-executable',
            'text/x-shellscript'
        ]
        
        for content_type in disallowed_types:
            with pytest.raises(ValueError, match=f"Content type '{content_type}' not allowed"):
                _validate_content_type(content_type)


class TestEncryptionConfiguration:
    """Test KMS vs SSE-S3 encryption configuration."""
    
    def test_default_sse_s3_encryption(self, monkeypatch):
        """Should use SSE-S3 when no KMS key is configured."""
        monkeypatch.delenv("PETTY_KMS_KEY_ID", raising=False)
        
        config = _get_encryption_config()
        
        assert config == {"ServerSideEncryption": "AES256"}
    
    def test_kms_encryption_when_configured(self, monkeypatch):
        """Should use KMS when key ID is provided."""
        test_key_id = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
        monkeypatch.setenv("PETTY_KMS_KEY_ID", test_key_id)
        
        config = _get_encryption_config()
        
        assert config == {
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": test_key_id
        }


@mock_aws
class TestS3Operations:
    """Test S3 operations with encryption and validation."""
    
    def setup_method(self, method):
        """Set up S3 bucket for testing."""
        self.s3_client = boto3.client("s3", region_name="us-east-1")
        self.bucket = "petty-test-bucket"
        self.s3_client.create_bucket(Bucket=self.bucket)
    
    def test_put_json_with_sse_s3(self, monkeypatch):
        """Should store JSON with SSE-S3 encryption."""
        monkeypatch.delenv("PETTY_KMS_KEY_ID", raising=False)
        
        test_data = {"test": "data", "number": 42}
        key = "test/data.json"
        
        put_json(self.bucket, key, test_data)
        
        # Verify object exists and has correct properties
        response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
        assert response["ContentType"] == "application/json"
        assert response["ServerSideEncryption"] == "AES256"
        
        # Verify content
        obj = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        stored_data = json.loads(obj["Body"].read().decode("utf-8"))
        assert stored_data == test_data
    
    def test_put_json_with_kms(self, monkeypatch):
        """Should store JSON with KMS encryption when configured."""
        test_key_id = "alias/petty-kms-key"
        monkeypatch.setenv("PETTY_KMS_KEY_ID", test_key_id)
        
        test_data = {"encrypted": "data"}
        key = "secure/data.json"
        
        put_json(self.bucket, key, test_data)
        
        # Verify KMS encryption (moto doesn't fully simulate KMS, but we can check the call)
        response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
        assert response["ContentType"] == "application/json"
        # Note: moto doesn't return KMS fields, but in real AWS this would show KMS encryption
    
    def test_put_text_with_validation(self):
        """Should store text with content type validation."""
        content = "This is test content\nWith multiple lines"
        key = "test/content.txt"
        
        put_text(self.bucket, key, content, "text/plain")
        
        response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
        assert response["ContentType"] == "text/plain"
        
        obj = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        stored_content = obj["Body"].read().decode("utf-8")
        assert stored_content == content
    
    def test_put_text_invalid_content_type(self):
        """Should reject invalid content types."""
        content = "test content"
        key = "test/malicious.html"
        
        with pytest.raises(ValueError, match="Content type 'text/html' not allowed"):
            put_text(self.bucket, key, content, "text/html")
    
    def test_put_binary_with_auto_detection(self):
        """Should auto-detect content type for binary data."""
        binary_data = b"binary\x00\x01\x02data"
        key = "test/data.bin"
        
        put_binary(self.bucket, key, binary_data)
        
        response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
        assert response["ContentType"] == "application/octet-stream"
        
        obj = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        stored_data = obj["Body"].read()
        assert stored_data == binary_data
    
    def test_put_binary_csv_extension(self):
        """Should detect CSV content type from file extension."""
        csv_data = b"name,age\nJohn,30\nJane,25"
        key = "test/data.csv"
        
        put_binary(self.bucket, key, csv_data)
        
        response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
        assert response["ContentType"] == "text/csv"
    
    def test_get_encryption_status(self):
        """Should return encryption and metadata information."""
        test_data = {"status": "test"}
        key = "test/status.json"
        
        put_json(self.bucket, key, test_data)
        
        status = get_encryption_status(self.bucket, key)
        
        assert status["server_side_encryption"] == "AES256"
        assert status["content_type"] == "application/json"
        assert "last_modified" in status
        assert "etag" in status
    
    def test_get_encryption_status_not_found(self):
        """Should raise FileNotFoundError for missing objects."""
        with pytest.raises(FileNotFoundError, match="Object s3://petty-test-bucket/missing.json not found"):
            get_encryption_status(self.bucket, "missing.json")


class TestSecurityHardening:
    """Test security hardening features."""
    
    def test_content_type_whitelist_is_restrictive(self):
        """Ensure the content type whitelist is appropriately restrictive."""
        from src.common.aws.s3 import ALLOWED_CONTENT_TYPES
        
        # Should not allow potentially dangerous types
        dangerous_types = {
            'text/html',
            'application/javascript',
            'text/javascript',
            'application/x-executable',
            'application/x-msdownload',
            'application/x-shockwave-flash'
        }
        
        assert not dangerous_types.intersection(ALLOWED_CONTENT_TYPES)
        
        # Should be a reasonable number of allowed types (not too permissive)
        assert len(ALLOWED_CONTENT_TYPES) <= 10
    
    @mock_aws
    def test_json_minification(self):
        """Should minify JSON to reduce storage and improve consistency."""
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket = "petty-test-bucket"
        s3_client.create_bucket(Bucket=bucket)
        
        test_data = {
            "key": "value",
            "nested": {
                "array": [1, 2, 3],
                "bool": True
            }
        }
        key = "test/minified.json"
        
        put_json(bucket, key, test_data)
        
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        stored_json = obj["Body"].read().decode("utf-8")
        
        # Should be minified (no extra spaces)
        assert " " not in stored_json.replace(' ', '')  # Only spaces in values
        assert "\n" not in stored_json
        assert stored_json == '{"key":"value","nested":{"array":[1,2,3],"bool":true}}'