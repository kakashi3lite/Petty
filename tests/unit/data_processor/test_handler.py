"""
Unit tests for data processor handler with valid/invalid payload tests.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

# Mock Lambda context
class MockLambdaContext:
    def __init__(self):
        self.aws_request_id = "test-request-id"


class TestDataProcessorHandler(unittest.TestCase):
    """Test the data processor Lambda handler."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_payload = {
            "collar_id": "SN-12345",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.0060, 40.7128]
            }
        }
        
        self.valid_event = {
            "body": json.dumps(self.valid_payload)
        }
        
        self.context = MockLambdaContext()
        
        # Import the module here so path is set
        try:
            import data_processor.app
            self.app_module = data_processor.app
        except ImportError:
            self.app_module = None
        
    @patch('sys.path', ['/home/runner/work/Petty/Petty/src'] + sys.path)
    @patch('data_processor.app.write_records')
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_valid_payload_success(self, mock_write_records, mock_path):
        """Test handler with valid payload returns 200 with {ok: true}."""
        if self.app_module is None:
            self.skipTest("data_processor module not available")
            
        # Setup mock
        mock_write_records.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        
        result = self.app_module.lambda_handler(self.valid_event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["ok"], True)
        
        # Verify Timestream was called
        mock_write_records.assert_called_once()
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_missing_required_field(self):
        """Test handler with missing required field returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Remove required field
        invalid_payload = self.valid_payload.copy()
        del invalid_payload["collar_id"]
        
        event = {"body": json.dumps(invalid_payload)}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertIn("collar_id", body["error"])
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_invalid_heart_rate(self):
        """Test handler with invalid heart rate returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Invalid heart rate
        invalid_payload = self.valid_payload.copy()
        invalid_payload["heart_rate"] = 400  # Too high
        
        event = {"body": json.dumps(invalid_payload)}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertIn("heart_rate", body["error"])
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_invalid_activity_level(self):
        """Test handler with invalid activity level returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Invalid activity level
        invalid_payload = self.valid_payload.copy()
        invalid_payload["activity_level"] = 5  # Must be 0, 1, or 2
        
        event = {"body": json.dumps(invalid_payload)}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertIn("activity_level", body["error"])
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_invalid_timestamp_format(self):
        """Test handler with invalid timestamp format returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Invalid timestamp format
        invalid_payload = self.valid_payload.copy()
        invalid_payload["timestamp"] = "2024-01-15"  # Not ISO8601
        
        event = {"body": json.dumps(invalid_payload)}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertIn("timestamp", body["error"])
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_invalid_geojson_location(self):
        """Test handler with invalid GeoJSON location returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Invalid location - not a Point
        invalid_payload = self.valid_payload.copy()
        invalid_payload["location"] = {
            "type": "LineString",
            "coordinates": [[-74.0060, 40.7128], [-74.0061, 40.7129]]
        }
        
        event = {"body": json.dumps(invalid_payload)}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertIn("Point", body["error"])
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_invalid_coordinates_range(self):
        """Test handler with coordinates out of range returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Invalid coordinates - longitude out of range
        invalid_payload = self.valid_payload.copy()
        invalid_payload["location"]["coordinates"] = [200, 40]  # Invalid longitude
        
        event = {"body": json.dumps(invalid_payload)}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_invalid_json_body(self):
        """Test handler with invalid JSON body returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Invalid JSON
        event = {"body": "invalid json {"}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertIn("JSON", body["error"])
        
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_non_dict_body(self):
        """Test handler with non-dict body returns 400."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Non-dict body
        event = {"body": json.dumps(["not", "a", "dict"])}
        result = lambda_handler(event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        self.assertIn("format", body["error"])
        
    @patch('data_processor.app.write_records')
    @patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False)
    def test_timestream_error_handling(self, mock_write_records):
        """Test handler with Timestream error returns 500."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        # Setup mock to raise error
        mock_write_records.side_effect = Exception("Timestream error")
        
        result = lambda_handler(self.valid_event, self.context)
        
        # Check response
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertIn("error", body)
        
    def test_cors_headers_included(self):
        """Test that CORS headers are included in response."""
        try:
            from data_processor.app import lambda_handler
        except ImportError:
            self.skipTest("data_processor module not available")
            
        with patch('data_processor.app.write_records'):
            with patch('data_processor.app.SECURITY_MODULES_AVAILABLE', False):
                result = lambda_handler(self.valid_event, self.context)
                
                # Check CORS headers
                headers = result.get("headers", {})
                self.assertIn("Access-Control-Allow-Origin", headers)
                self.assertIn("Access-Control-Allow-Headers", headers)
                self.assertIn("Access-Control-Allow-Methods", headers)


if __name__ == '__main__':
    unittest.main()