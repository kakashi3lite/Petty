"""
Integration tests for Lambda handlers with new Pydantic v2 models
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch

# Import the handler modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processor.app import lambda_handler as data_processor_handler
from timeline_generator.app import lambda_handler as timeline_generator_handler
from feedback_handler.app import lambda_handler as feedback_handler


class TestDataProcessorHandler:
    """Test cases for data processor handler with TelemetryIn model."""
    
    @patch('data_processor.app.timestream_client')
    def test_valid_telemetry_data(self, mock_timestream):
        """Test successful telemetry data processing."""
        mock_timestream.write_records.return_value = {"RecordId": "test_record_123"}
        
        event = {
            "body": json.dumps({
                "collar_id": "AB-123456",
                "timestamp": "2024-01-15T10:30:00Z",
                "heart_rate": 85,
                "activity_level": 1,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.0060, 40.7128]
                }
            })
        }
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = data_processor_handler(event, context)
        
        assert response["statusCode"] == 200
        assert "success" in json.loads(response["body"])
    
    def test_invalid_telemetry_data(self):
        """Test validation error handling."""
        event = {
            "body": json.dumps({
                "collar_id": "invalid",  # Invalid format
                "timestamp": "2024-01-15T10:30:00Z",
                "heart_rate": 85,
                "activity_level": 1,
                "location": {
                    "type": "Point", 
                    "coordinates": [-74.0060, 40.7128]
                }
            })
        }
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = data_processor_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body or not body["success"]
    
    def test_malformed_json(self):
        """Test malformed JSON handling."""
        event = {"body": "invalid json{"}
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = data_processor_handler(event, context)
        
        assert response["statusCode"] == 400


class TestTimelineGeneratorHandler:
    """Test cases for timeline generator handler with CollarIdQuery model."""
    
    def test_valid_collar_query(self):
        """Test successful timeline generation."""
        event = {
            "queryStringParameters": {
                "collar_id": "AB-123456"
            }
        }
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = timeline_generator_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "data" in body or "timeline" in body
    
    def test_invalid_collar_id(self):
        """Test validation error for invalid collar ID."""
        event = {
            "queryStringParameters": {
                "collar_id": "invalid"  # Invalid format
            }
        }
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = timeline_generator_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_missing_query_parameters(self):
        """Test handling of missing query parameters."""
        event = {"queryStringParameters": None}
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = timeline_generator_handler(event, context)
        
        # Should default or return validation error
        assert response["statusCode"] in [200, 400]


class TestFeedbackHandler:
    """Test cases for feedback handler with FeedbackIn model."""
    
    def test_valid_feedback(self):
        """Test successful feedback processing."""
        event = {
            "body": json.dumps({
                "event_id": "evt_12345678",
                "user_feedback": "correct"
            })
        }
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = feedback_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "success" in body or "ok" in body
    
    def test_invalid_event_id(self):
        """Test validation error for invalid event ID."""
        event = {
            "body": json.dumps({
                "event_id": "invalid",  # Invalid format
                "user_feedback": "correct"
            })
        }
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = feedback_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_invalid_feedback_value(self):
        """Test validation error for invalid feedback value."""
        event = {
            "body": json.dumps({
                "event_id": "evt_12345678",
                "user_feedback": "invalid"  # Invalid value
            })
        }
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = feedback_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
    
    def test_malformed_json(self):
        """Test malformed JSON handling."""
        event = {"body": "invalid json{"}
        
        context = Mock()
        context.aws_request_id = "test_request_123"
        
        response = feedback_handler(event, context)
        
        assert response["statusCode"] == 400