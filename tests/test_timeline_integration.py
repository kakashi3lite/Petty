#!/usr/bin/env python3
"""
Integration test for timeline generator with Timestream 24h query
"""

import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_timeline_lambda_with_stub_data():
    """Test timeline Lambda handler with stub data"""
    print("Testing timeline Lambda handler with stub data...")
    
    # Set environment to use stub data
    os.environ['USE_STUB_DATA'] = 'true'
    
    try:
        # Mock the powertools imports to avoid dependency issues
        with patch.dict('sys.modules', {
            'common.observability.powertools': MagicMock(),
            'behavioral_interpreter.interpreter': MagicMock()
        }):
            # Create a mock for BehavioralInterpreter
            mock_interpreter = MagicMock()
            mock_interpreter.analyze_timeline.return_value = [
                {
                    "event_id": "evt_12345678", 
                    "timestamp": "2023-12-07T10:30:00Z",
                    "behavior": "Walking detected",
                    "confidence": 0.85
                }
            ]
            
            # Mock the behavioral interpreter class
            sys.modules['behavioral_interpreter.interpreter'].BehavioralInterpreter = lambda: mock_interpreter
            
            # Mock powertools components
            mock_logger = MagicMock()
            mock_tracer = MagicMock()
            mock_metrics = MagicMock()
            mock_MetricUnit = MagicMock()
            
            sys.modules['common.observability.powertools'].logger = mock_logger
            sys.modules['common.observability.powertools'].tracer = mock_tracer  
            sys.modules['common.observability.powertools'].metrics = mock_metrics
            sys.modules['common.observability.powertools'].MetricUnit = mock_MetricUnit
            
            # Make decorators no-ops
            mock_tracer.capture_lambda_handler = lambda x: x
            mock_logger.inject_lambda_context = lambda **kwargs: lambda x: x
            
            # Now import and test the timeline generator
            from timeline_generator.app import lambda_handler
            
            # Create test event
            event = {
                "queryStringParameters": {
                    "collar_id": "SN-123"
                }
            }
            context = MagicMock()
            
            # Call the handler
            result = lambda_handler(event, context)
            
            # Validate response
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert 'collar_id' in body
            assert 'timeline' in body
            assert body['collar_id'] == 'SN-123'
            
            # Verify BehavioralInterpreter was called
            mock_interpreter.analyze_timeline.assert_called_once()
            
            # Check that data was passed to interpreter
            call_args = mock_interpreter.analyze_timeline.call_args[0][0]
            assert len(call_args) > 0  # Should have data
            assert call_args[0]['collar_id'] == 'SN-123'
            
            print("✓ Timeline Lambda handler works with stub data")
            return True
            
    finally:
        # Cleanup
        if 'USE_STUB_DATA' in os.environ:
            del os.environ['USE_STUB_DATA']

def test_timeline_lambda_with_timestream_fallback():
    """Test timeline Lambda handler falls back to stub when Timestream fails"""
    print("Testing timeline Lambda handler with Timestream fallback...")
    
    # Set environment to use Timestream (but we'll make it fail)
    os.environ['USE_STUB_DATA'] = 'false'
    
    try:
        # Mock the imports
        with patch.dict('sys.modules', {
            'common.observability.powertools': MagicMock(),
            'behavioral_interpreter.interpreter': MagicMock()
        }):
            # Mock Timestream to fail
            with patch('boto3.Session') as mock_session:
                mock_client = MagicMock()
                mock_client.query.side_effect = Exception("Timestream connection failed")
                mock_session.return_value.client.return_value = mock_client
                
                # Mock the behavioral interpreter  
                mock_interpreter = MagicMock()
                mock_interpreter.analyze_timeline.return_value = [
                    {"event_id": "evt_fallback", "behavior": "Fallback data processed"}
                ]
                sys.modules['behavioral_interpreter.interpreter'].BehavioralInterpreter = lambda: mock_interpreter
                
                # Mock powertools
                mock_logger = MagicMock()
                mock_tracer = MagicMock()
                mock_metrics = MagicMock()
                mock_MetricUnit = MagicMock()
                
                sys.modules['common.observability.powertools'].logger = mock_logger
                sys.modules['common.observability.powertools'].tracer = mock_tracer
                sys.modules['common.observability.powertools'].metrics = mock_metrics
                sys.modules['common.observability.powertools'].MetricUnit = mock_MetricUnit
                
                # Make decorators no-ops
                mock_tracer.capture_lambda_handler = lambda x: x
                mock_logger.inject_lambda_context = lambda **kwargs: lambda x: x
                
                # Import and test
                from timeline_generator.app import lambda_handler
                
                event = {"queryStringParameters": {"collar_id": "SN-456"}}
                context = MagicMock()
                
                result = lambda_handler(event, context)
                
                # Should still succeed with fallback data
                assert result['statusCode'] == 200
                body = json.loads(result['body'])
                assert body['collar_id'] == 'SN-456'
                
                # Verify error was logged and metrics recorded
                mock_logger.error.assert_called()
                
                print("✓ Timeline Lambda handler falls back gracefully on Timestream failure")
                return True
                
    finally:
        if 'USE_STUB_DATA' in os.environ:
            del os.environ['USE_STUB_DATA']

def run_integration_tests():
    """Run integration tests"""
    tests = [
        test_timeline_lambda_with_stub_data,
        test_timeline_lambda_with_timestream_fallback
    ]
    
    passed = 0
    failed = 0
    
    print("="*60)
    print("Running Timeline Generator Integration Tests")
    print("="*60)
    
    for test in tests:
        try:
            print(f"\nRunning {test.__name__}...")
            if test():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} returned False")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Integration Test Results: {passed} passed, {failed} failed") 
    print(f"{'='*60}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)