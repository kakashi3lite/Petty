"""
Tests for feedback handler S3 integration with SSE encryption.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from feedback_handler.app import lambda_handler, _extract_collar_id_from_event_id, _simulate_raw_segment
    from common.aws.s3 import put_json
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Module import failed: {e}")
    MODULES_AVAILABLE = False


class TestFeedbackHandlerS3Integration:
    """Test feedback handler S3 integration"""
    
    def test_extract_collar_id_from_event_id(self):
        """Test collar_id extraction from event_id"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
        
        # Test valid event_id formats
        assert _extract_collar_id_from_event_id("evt_SN-123_1234567890") == "SN-123"
        assert _extract_collar_id_from_event_id("evt_SN-1A4B7C-9Z_1234567890") == "SN-1A4B7C-9Z"
        assert _extract_collar_id_from_event_id("evt_COLLAR-001_1234567890") == "COLLAR-001"
        
        # Test invalid formats
        assert _extract_collar_id_from_event_id("invalid_format") is None
        assert _extract_collar_id_from_event_id("evt_") is None
        assert _extract_collar_id_from_event_id("") is None
        
    def test_simulate_raw_segment(self):
        """Test raw segment simulation"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
            
        event_id = "evt_SN-123_1234567890"
        collar_id = "SN-123"
        
        segment = _simulate_raw_segment(event_id, collar_id)
        
        # Verify required fields
        assert segment["collar_id"] == collar_id
        assert segment["event_id"] == event_id
        assert "timestamp" in segment
        assert "heart_rate" in segment
        assert "activity_level" in segment
        assert "location" in segment
        
        # Verify data types and ranges
        assert isinstance(segment["heart_rate"], int)
        assert isinstance(segment["activity_level"], int)
        assert segment["activity_level"] in [0, 1, 2]
        assert segment["location"]["type"] == "Point"
        assert len(segment["location"]["coordinates"]) == 2
        
    @patch('common.aws.s3.s3_client')
    def test_put_json_with_sse(self, mock_s3_client):
        """Test put_json function with SSE encryption"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
            
        # Mock S3 response
        mock_response = {
            'ETag': '"abc123"',
            'ServerSideEncryption': 'AES256'
        }
        mock_s3_client.put_object.return_value = mock_response
        
        # Test data
        test_data = {
            "event_id": "evt_SN-123_1234567890",
            "collar_id": "SN-123",
            "user_feedback": "correct"
        }
        
        bucket = "test-bucket"
        key = "feedback/SN-123/evt_SN-123_1234567890.json"
        
        # Call put_json
        result = put_json(bucket, key, test_data)
        
        # Verify S3 call was made with correct parameters
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args[1]
        
        assert call_args['Bucket'] == bucket
        assert call_args['Key'] == key
        assert call_args['ContentType'] == 'application/json'
        assert call_args['ServerSideEncryption'] == 'AES256'
        
        # Verify JSON content
        body_data = json.loads(call_args['Body'])
        assert body_data == test_data
        
        # Verify response
        assert result == mock_response
        
    @patch('feedback_handler.app.put_json')
    @patch('feedback_handler.app._simulate_raw_segment')
    def test_lambda_handler_success(self, mock_simulate, mock_put_json):
        """Test successful feedback processing with S3 storage"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
            
        # Mock dependencies
        mock_raw_segment = {
            "collar_id": "SN-123",
            "timestamp": "2025-01-18T12:00:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]},
            "event_id": "evt_SN-123_1234567890"
        }
        mock_simulate.return_value = mock_raw_segment
        
        mock_s3_response = {
            'ETag': '"abc123"',
            'ServerSideEncryption': 'AES256'
        }
        mock_put_json.return_value = mock_s3_response
        
        # Test event
        event = {
            "body": json.dumps({
                "event_id": "evt_SN-123_1234567890",
                "user_feedback": "correct"
            })
        }
        context = Mock()
        
        # Call lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['ok'] is True
        assert 's3_key' in body
        assert body['s3_key'] == "feedback/SN-123/evt_SN-123_1234567890.json"
        assert 'etag' in body
        
        # Verify S3 put_json was called correctly
        mock_put_json.assert_called_once()
        call_args = mock_put_json.call_args
        
        # Check bucket and key
        assert call_args[1]['bucket'] == 'petty-feedback-dev'  # Default bucket
        assert call_args[1]['key'] == "feedback/SN-123/evt_SN-123_1234567890.json"
        
        # Check stored data structure
        stored_data = call_args[1]['data']
        assert stored_data['event_id'] == "evt_SN-123_1234567890"
        assert stored_data['collar_id'] == "SN-123"
        assert stored_data['user_feedback'] == "correct"
        assert stored_data['raw_segment'] == mock_raw_segment
        assert 'labeled_at' in stored_data
        
        # Check metadata
        metadata = call_args[1]['metadata']
        assert metadata['feedback-type'] == "correct"
        assert metadata['collar-id'] == "SN-123"
        assert metadata['event-id'] == "evt_SN-123_1234567890"
        
    def test_lambda_handler_invalid_payload(self):
        """Test lambda handler with invalid payloads"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
            
        # Test missing event_id
        event = {
            "body": json.dumps({
                "user_feedback": "correct"
            })
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        
        # Test invalid feedback value
        event = {
            "body": json.dumps({
                "event_id": "evt_SN-123_1234567890",
                "user_feedback": "maybe"
            })
        }
        
        response = lambda_handler(event, context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        
    def test_lambda_handler_with_explicit_collar_id(self):
        """Test lambda handler when collar_id is provided explicitly"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
            
        with patch('feedback_handler.app.put_json') as mock_put_json, \
             patch('feedback_handler.app._simulate_raw_segment') as mock_simulate:
            
            mock_simulate.return_value = {}
            mock_put_json.return_value = {'ETag': '"abc123"'}
            
            event = {
                "body": json.dumps({
                    "event_id": "custom_event_123",
                    "collar_id": "CUSTOM-COLLAR-456",
                    "user_feedback": "incorrect"
                })
            }
            context = Mock()
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['s3_key'] == "feedback/CUSTOM-COLLAR-456/custom_event_123.json"
            
            # Verify the correct collar_id was used
            call_args = mock_put_json.call_args
            stored_data = call_args[1]['data']
            assert stored_data['collar_id'] == "CUSTOM-COLLAR-456"
            
    @patch('common.aws.s3.s3_client')
    def test_put_json_client_error(self, mock_s3_client):
        """Test put_json handling of S3 client errors"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
            
        from botocore.exceptions import ClientError
        
        # Mock S3 client error
        mock_s3_client.put_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket does not exist'}},
            operation_name='PutObject'
        )
        
        test_data = {"test": "data"}
        
        with pytest.raises(ClientError):
            put_json("nonexistent-bucket", "test/key.json", test_data)
            
    def test_deterministic_s3_key_format(self):
        """Test that S3 keys follow the deterministic format"""
        if not MODULES_AVAILABLE:
            pytest.skip("Modules not available")
            
        with patch('feedback_handler.app.put_json') as mock_put_json, \
             patch('feedback_handler.app._simulate_raw_segment'):
            
            mock_put_json.return_value = {'ETag': '"abc123"'}
            
            test_cases = [
                ("evt_SN-123_1234567890", "SN-123", "feedback/SN-123/evt_SN-123_1234567890.json"),
                ("evt_COLLAR-ABC-XYZ_9876543210", "COLLAR-ABC-XYZ", "feedback/COLLAR-ABC-XYZ/evt_COLLAR-ABC-XYZ_9876543210.json"),
            ]
            
            for event_id, expected_collar_id, expected_key in test_cases:
                event = {
                    "body": json.dumps({
                        "event_id": event_id,
                        "user_feedback": "correct"
                    })
                }
                context = Mock()
                
                response = lambda_handler(event, context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['s3_key'] == expected_key
                
                # Verify put_json was called with correct key
                call_args = mock_put_json.call_args
                assert call_args[1]['key'] == expected_key