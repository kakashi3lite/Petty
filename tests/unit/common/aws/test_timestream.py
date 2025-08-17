"""
Unit tests for Timestream helper module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src'))

try:
    from common.aws.timestream import build_collar_record, TimestreamWriter, write_records
except ImportError:
    # Handle case where modules aren't available
    build_collar_record = None
    TimestreamWriter = None
    write_records = None


class TestBuildCollarRecord(unittest.TestCase):
    """Test the build_collar_record function."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_location = {
            "type": "Point",
            "coordinates": [-74.0060, 40.7128]  # NYC coordinates
        }
        
    def test_build_valid_record(self):
        """Test building a valid collar record."""
        if build_collar_record is None:
            self.skipTest("timestream module not available")
            
        record = build_collar_record(
            collar_id="SN-12345",
            timestamp="2024-01-15T10:30:00Z",
            heart_rate=85,
            activity_level=1,
            location=self.valid_location,
            environment="test"
        )
        
        # Check record structure
        self.assertIn('Time', record)
        self.assertIn('TimeUnit', record)
        self.assertIn('Dimensions', record)
        self.assertIn('MeasureName', record)
        self.assertIn('MeasureValueType', record)
        self.assertIn('MeasureValues', record)
        
        # Check dimensions
        dimensions = {d['Name']: d['Value'] for d in record['Dimensions']}
        self.assertEqual(dimensions['CollarId'], 'SN-12345')
        self.assertEqual(dimensions['Environment'], 'test')
        
        # Check measures
        measures = {m['Name']: m['Value'] for m in record['MeasureValues']}
        self.assertEqual(measures['HeartRate'], '85')
        self.assertEqual(measures['ActivityLevel'], '1')
        self.assertEqual(float(measures['Longitude']), -74.0060)
        self.assertEqual(float(measures['Latitude']), 40.7128)
        
    def test_invalid_collar_id(self):
        """Test validation of collar_id parameter."""
        if build_collar_record is None:
            self.skipTest("timestream module not available")
            
        # Empty string
        with self.assertRaises(ValueError) as cm:
            build_collar_record("", "2024-01-15T10:30:00Z", 85, 1, self.valid_location)
        self.assertIn("collar_id", str(cm.exception))
        
        # None
        with self.assertRaises(ValueError) as cm:
            build_collar_record(None, "2024-01-15T10:30:00Z", 85, 1, self.valid_location)
        self.assertIn("collar_id", str(cm.exception))
        
        # Not a string
        with self.assertRaises(ValueError) as cm:
            build_collar_record(12345, "2024-01-15T10:30:00Z", 85, 1, self.valid_location)
        self.assertIn("collar_id", str(cm.exception))
        
    def test_invalid_heart_rate(self):
        """Test validation of heart_rate parameter."""
        if build_collar_record is None:
            self.skipTest("timestream module not available")
            
        # Too low
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 25, 1, self.valid_location)
        self.assertIn("heart_rate", str(cm.exception))
        
        # Too high
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 350, 1, self.valid_location)
        self.assertIn("heart_rate", str(cm.exception))
        
        # Not an integer
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", "85", 1, self.valid_location)
        self.assertIn("heart_rate", str(cm.exception))
        
    def test_invalid_activity_level(self):
        """Test validation of activity_level parameter."""
        if build_collar_record is None:
            self.skipTest("timestream module not available")
            
        # Invalid value
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 85, 3, self.valid_location)
        self.assertIn("activity_level", str(cm.exception))
        
        # Not an integer
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 85, "1", self.valid_location)
        self.assertIn("activity_level", str(cm.exception))
        
    def test_invalid_location(self):
        """Test validation of location parameter."""
        if build_collar_record is None:
            self.skipTest("timestream module not available")
            
        # Not a dict
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 85, 1, "invalid")
        self.assertIn("location", str(cm.exception))
        
        # Missing type
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 85, 1, {})
        self.assertIn("location", str(cm.exception))
        
        # Wrong type
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 85, 1, {"type": "LineString"})
        self.assertIn("Point", str(cm.exception))
        
        # Invalid coordinates
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 85, 1, {
                "type": "Point",
                "coordinates": [-74.0060]  # Missing latitude
            })
        self.assertIn("coordinates", str(cm.exception))
        
        # Out of range coordinates
        with self.assertRaises(ValueError) as cm:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 85, 1, {
                "type": "Point",
                "coordinates": [200, 40]  # Invalid longitude
            })
        self.assertIn("range", str(cm.exception))


class TestTimestreamWriter(unittest.TestCase):
    """Test the TimestreamWriter class."""
    
    @patch('common.aws.timestream.BOTO3_AVAILABLE', True)
    @patch('common.aws.timestream.boto3')
    def test_write_records_success(self, mock_boto3):
        """Test successful record writing."""
        if TimestreamWriter is None:
            self.skipTest("timestream module not available")
            
        # Setup mock
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.write_records.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        
        writer = TimestreamWriter()
        
        test_records = [{"Time": "1640995200000", "TimeUnit": "MILLISECONDS"}]
        result = writer.write_records("TestDB", "TestTable", test_records)
        
        # Verify call
        mock_client.write_records.assert_called_once_with(
            DatabaseName="TestDB",
            TableName="TestTable", 
            Records=test_records
        )
        
        self.assertEqual(result["ResponseMetadata"]["HTTPStatusCode"], 200)
        
    def test_write_records_validation(self):
        """Test parameter validation."""
        if TimestreamWriter is None:
            self.skipTest("timestream module not available")
            
        writer = TimestreamWriter()
        
        # Empty database
        with self.assertRaises(ValueError) as cm:
            writer.write_records("", "TestTable", [{}])
        self.assertIn("Database", str(cm.exception))
        
        # Empty table
        with self.assertRaises(ValueError) as cm:
            writer.write_records("TestDB", "", [{}])
        self.assertIn("Table", str(cm.exception))
        
        # Empty records
        with self.assertRaises(ValueError) as cm:
            writer.write_records("TestDB", "TestTable", [])
        self.assertIn("Records", str(cm.exception))


class TestWriteRecordsFunction(unittest.TestCase):
    """Test the write_records convenience function."""
    
    @patch('common.aws.timestream.get_timestream_writer')
    def test_write_records_function(self, mock_get_writer):
        """Test the write_records convenience function."""
        if write_records is None:
            self.skipTest("timestream module not available")
            
        # Setup mock
        mock_writer = MagicMock()
        mock_get_writer.return_value = mock_writer
        mock_writer.write_records.return_value = {"success": True}
        
        test_records = [{"Time": "1640995200000"}]
        result = write_records("TestDB", "TestTable", test_records, "us-west-2")
        
        # Verify calls
        mock_get_writer.assert_called_once_with("us-west-2")
        mock_writer.write_records.assert_called_once_with("TestDB", "TestTable", test_records)
        
        self.assertEqual(result["success"], True)


if __name__ == '__main__':
    unittest.main()