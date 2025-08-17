"""
Unit tests for Timestream query functionality
"""

import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestTimestreamQuery:
    """Test Timestream query functionality"""
    
    def test_timestream_query_with_mock_data(self):
        """Test querying Timestream with mocked client returns expected data format"""
        # Mock Timestream response data
        mock_response = {
            'Rows': [
                {
                    'Data': [
                        {'ScalarValue': 'SN-123'},  # CollarId
                        {'ScalarValue': '2023-12-07T10:00:00.000000000Z'},  # timestamp
                        {'ScalarValue': 'HeartRate'},  # measure_name
                        {'ScalarValue': '75.0'}  # measure_value
                    ]
                },
                {
                    'Data': [
                        {'ScalarValue': 'SN-123'},  # CollarId
                        {'ScalarValue': '2023-12-07T10:00:00.000000000Z'},  # timestamp
                        {'ScalarValue': 'ActivityLevel'},  # measure_name
                        {'ScalarValue': '1.0'}  # measure_value
                    ]
                },
                {
                    'Data': [
                        {'ScalarValue': 'SN-123'},  # CollarId
                        {'ScalarValue': '2023-12-07T10:00:00.000000000Z'},  # timestamp
                        {'ScalarValue': 'Longitude'},  # measure_name
                        {'ScalarValue': '-74.0060'}  # measure_value
                    ]
                },
                {
                    'Data': [
                        {'ScalarValue': 'SN-123'},  # CollarId
                        {'ScalarValue': '2023-12-07T10:00:00.000000000Z'},  # timestamp
                        {'ScalarValue': 'Latitude'},  # measure_name
                        {'ScalarValue': '40.7128'}  # measure_value
                    ]
                }
            ]
        }
        
        # Mock the Timestream client
        with patch('boto3.Session') as mock_session:
            mock_client = MagicMock()
            mock_client.query.return_value = mock_response
            mock_session.return_value.client.return_value = mock_client
            
            # Import and test the query function
            from common.aws.timestream import query_last_24h
            
            result = query_last_24h('SN-123')
            
            # Verify the result
            assert len(result) == 1, f"Expected 1 record, got {len(result)}"
            
            record = result[0]
            assert record['collar_id'] == 'SN-123'
            assert record['heart_rate'] == 75
            assert record['activity_level'] == 1
            assert record['location']['type'] == 'Point'
            assert record['location']['coordinates'] == [-74.0060, 40.7128]
            assert 'timestamp' in record
            
            print("✓ Timestream query returns correctly formatted data")
    
    def test_timeline_generator_with_stub_data(self):
        """Test timeline generator with stub data enabled"""
        # Set environment variable to use stub data
        os.environ['USE_STUB_DATA'] = 'true'
        
        try:
            from timeline_generator.app import _get_last_24h_data
            
            result = _get_last_24h_data('SN-123')
            
            # Verify stub data structure
            assert len(result) > 0, "Stub data should return records"
            
            record = result[0]
            assert 'collar_id' in record
            assert 'timestamp' in record
            assert 'heart_rate' in record
            assert 'activity_level' in record
            assert 'location' in record
            assert record['location']['type'] == 'Point'
            assert 'coordinates' in record['location']
            
            print("✓ Timeline generator with stub data returns correct format")
            
        finally:
            # Clean up environment variable
            if 'USE_STUB_DATA' in os.environ:
                del os.environ['USE_STUB_DATA']
    
    def test_timeline_generator_with_timestream_fallback(self):
        """Test timeline generator falls back to stub data when Timestream fails"""
        # Set environment to use Timestream
        os.environ['USE_STUB_DATA'] = 'false'
        
        try:
            # Mock Timestream client to raise an exception
            with patch('boto3.Session') as mock_session:
                mock_client = MagicMock()
                mock_client.query.side_effect = Exception("Timestream connection failed")
                mock_session.return_value.client.return_value = mock_client
                
                from timeline_generator.app import _get_last_24h_data
                
                result = _get_last_24h_data('SN-123')
                
                # Should fallback to stub data
                assert len(result) > 0, "Should fallback to stub data"
                
                record = result[0]
                assert record['collar_id'] == 'SN-123'
                
                print("✓ Timeline generator falls back to stub data on Timestream failure")
                
        finally:
            # Clean up environment variable
            if 'USE_STUB_DATA' in os.environ:
                del os.environ['USE_STUB_DATA']
    
    def test_behavioral_interpreter_with_timeline_data(self):
        """Test that BehavioralInterpreter can process timeline data"""
        try:
            from behavioral_interpreter.interpreter import BehavioralInterpreter
            from timeline_generator.app import _stub_last_24h
            
            # Get some test data
            test_data = _stub_last_24h('SN-123')
            
            # Process through behavioral interpreter
            interpreter = BehavioralInterpreter()
            timeline = interpreter.analyze_timeline(test_data)
            
            # Should return a list (even if empty)
            assert isinstance(timeline, list), "Timeline should be a list"
            
            print(f"✓ BehavioralInterpreter processed {len(test_data)} records into {len(timeline)} events")
            
        except ImportError:
            print("⚠ BehavioralInterpreter not available for testing")

def run_all_tests():
    """Run all tests"""
    test_class = TestTimestreamQuery()
    
    tests = [
        test_class.test_timestream_query_with_mock_data,
        test_class.test_timeline_generator_with_stub_data,
        test_class.test_timeline_generator_with_timestream_fallback,
        test_class.test_behavioral_interpreter_with_timeline_data
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\nRunning {test.__name__}...")
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)