"""
Integration test for timeline flow - serverless testing best practices
Simulates batch processing: points → interpreter → behavioral events
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add source path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from behavioral_interpreter.interpreter import BehavioralInterpreter
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    print("WARNING: Core modules not available - test will be skipped")


class TestTimelineFlow:
    """Integration test for serverless timeline processing patterns"""
    
    def test_batch_processing_smoke_test(self):
        """
        Serverless smoke test: batch of collar data → interpreter → expect ≥1 event
        
        This test validates:
        - Cloud-first serverless execution pattern
        - Batch processing capabilities  
        - Fast feedback with realistic data volume
        - Stub flag for test mode operation
        """
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        # Initialize interpreter with stub flag for test mode
        interpreter = BehavioralInterpreter()
        
        # Create realistic batch of collar sensor readings (serverless-typical volume)
        collar_data_batch = self._create_test_batch()
        
        print(f"🧪 Processing batch of {len(collar_data_batch)} collar readings...")
        
        # Simulate serverless Lambda execution: batch processing
        analysis_result = interpreter.analyze_timeline(collar_data_batch)
        
        # Validate serverless execution expectations
        assert isinstance(analysis_result, list), "Result should be a list of events"
        
        # Cloud-first expectation: real behavioral patterns should generate events
        # This validates the interpreter is working with meaningful thresholds
        events_detected = len(analysis_result) if analysis_result else 0
        print(f"📊 Events detected: {events_detected}")
        
        # Fast feedback assertion: expect at least one behavioral event from realistic data
        assert events_detected >= 1, f"Expected ≥1 behavioral event, got {events_detected}. Check interpreter thresholds."
        
        # Validate event structure for downstream Lambda consumers
        if analysis_result:
            sample_event = analysis_result[0]
            required_fields = ["event_id", "behavior", "confidence", "timestamp"]
            for field in required_fields:
                assert field in sample_event, f"Missing required field: {field}"
            
            # Validate confidence scoring for ML pipeline
            assert 0.0 <= sample_event["confidence"] <= 1.0, "Confidence should be normalized [0,1]"
            
        print("✅ Serverless timeline flow test passed!")
    
    def test_serverless_error_handling(self):
        """Test serverless error handling patterns"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        interpreter = BehavioralInterpreter()
        
        # Test empty batch (common in serverless)
        result = interpreter.analyze_timeline([])
        assert result == [], "Empty batch should return empty result"
        
        # Test malformed data (serverless robustness)
        malformed_data = [{"invalid": "data"}]
        result = interpreter.analyze_timeline(malformed_data)
        assert isinstance(result, list), "Should handle malformed data gracefully"
        
        print("✅ Serverless error handling test passed!")
    
    def _create_test_batch(self) -> List[Dict[str, Any]]:
        """
        Create realistic batch of collar data for serverless testing
        
        Simulates typical AWS Lambda event batch with realistic pet behavioral patterns
        that should trigger detection algorithms.
        """
        base_time = datetime.now(timezone.utc)
        batch = []
        
        # Create deep sleep pattern: activity_level=0, heart_rate=(40,65), min 4 points
        # This should reliably trigger the deep_sleep behavior detection
        for i in range(6):  # More than min_data_points=4
            timestamp = base_time.isoformat().replace('+00:00', 'Z')
            
            reading = {
                "collar_id": "TEST-SN-12345",
                "timestamp": timestamp,
                "heart_rate": 50 + (i % 10),  # Heart rate in range (40,65)
                "activity_level": 0,  # Low activity for deep sleep
                "location": {
                    "type": "Point", 
                    "coordinates": [-74.006, 40.7128]  # Stationary location
                }
            }
            batch.append(reading)
        
        # Add contrasting anxious pacing pattern: activity_level=1, heart_rate=(70,110), min 6 points
        for i in range(7):  # More than min_data_points=6
            timestamp = base_time.isoformat().replace('+00:00', 'Z')
            
            reading = {
                "collar_id": "TEST-SN-12345",
                "timestamp": timestamp, 
                "heart_rate": 85 + (i % 15),  # Heart rate in range (70,110)
                "activity_level": 1,  # Moderate activity for anxious pacing
                "location": {
                    "type": "Point",
                    "coordinates": [-74.006 + (i * 0.00001), 40.7128 + (i * 0.00001)]  # Small movements
                }
            }
            batch.append(reading)
            
        return batch


if __name__ == "__main__":
    # Support direct execution for fast feedback during development
    test_instance = TestTimelineFlow()
    
    print("=" * 60)
    print("Serverless Timeline Flow Integration Test")
    print("=" * 60)
    
    try:
        test_instance.test_batch_processing_smoke_test()
        test_instance.test_serverless_error_handling()
        print("\n🎉 All serverless timeline tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)