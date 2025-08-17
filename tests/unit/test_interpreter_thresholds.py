"""
Unit tests for interpreter threshold configuration and edge cases.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from behavioral_interpreter.interpreter import BehavioralInterpreter
    from behavioral_interpreter.config import InterpreterConfig
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False


class TestInterpreterThresholds(unittest.TestCase):
    """Test configurable thresholds in behavioral interpreter"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not MODULES_AVAILABLE:
            self.skipTest("Required modules not available")
        
        self.interpreter = BehavioralInterpreter()
    
    def test_deep_sleep_hr_variance_threshold_edge_cases(self):
        """Test deep sleep detection at HR variance threshold boundaries"""
        # Test data with low activity and heart rates
        base_data = [
            {
                "timestamp": f"2025-08-16T12:{i:02d}:00Z",
                "heart_rate": 50 + (i % 2),  # Variance will be 0.5
                "activity_level": 0,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            }
            for i in range(5)
        ]
        
        # Test just below threshold (should detect)
        with patch.object(self.interpreter.config, 'get_threshold', return_value=1.0):
            result = self.interpreter.analyze_timeline(base_data)
            deep_sleep_events = [e for e in result if e.get("behavior") == "Deep Sleep"]
            self.assertEqual(len(deep_sleep_events), 1, "Should detect deep sleep when variance < threshold")
        
        # Test just above threshold (should not detect)
        with patch.object(self.interpreter.config, 'get_threshold', return_value=0.3):
            result = self.interpreter.analyze_timeline(base_data)
            deep_sleep_events = [e for e in result if e.get("behavior") == "Deep Sleep"]
            self.assertEqual(len(deep_sleep_events), 0, "Should not detect deep sleep when variance >= threshold")
    
    def test_anxious_pacing_radius_threshold_edge_cases(self):
        """Test anxious pacing detection at radius threshold boundaries"""
        # Create data with small movement radius
        base_data = [
            {
                "timestamp": f"2025-08-16T12:{i:02d}:00Z",
                "heart_rate": 85,
                "activity_level": 1,
                "location": {
                    "type": "Point", 
                    "coordinates": [-74.006 + (i % 2) * 0.001, 40.7128]  # Radius ~0.0005
                }
            }
            for i in range(7)
        ]
        
        # Test just above radius (should detect)
        with patch.object(self.interpreter.config, 'get_threshold', return_value=0.0006):
            result = self.interpreter.analyze_timeline(base_data)
            pacing_events = [e for e in result if e.get("behavior") == "Anxious Pacing"]
            self.assertEqual(len(pacing_events), 1, "Should detect pacing when radius < threshold")
        
        # Test just below radius (should not detect)
        with patch.object(self.interpreter.config, 'get_threshold', return_value=0.0004):
            result = self.interpreter.analyze_timeline(base_data)
            pacing_events = [e for e in result if e.get("behavior") == "Anxious Pacing"]
            self.assertEqual(len(pacing_events), 0, "Should not detect pacing when radius >= threshold")
    
    def test_fetch_distance_threshold_edge_cases(self):
        """Test fetch detection at distance threshold boundaries"""
        # Create data with high->low activity cycles and sufficient distance
        base_data = [
            {
                "timestamp": "2025-08-16T12:00:00Z",
                "heart_rate": 120,
                "activity_level": 2,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            },
            {
                "timestamp": "2025-08-16T12:01:00Z",
                "heart_rate": 60,
                "activity_level": 0,
                "location": {"type": "Point", "coordinates": [-74.006 + 0.003, 40.7128]}  # Distance ~0.003
            },
            {
                "timestamp": "2025-08-16T12:02:00Z",
                "heart_rate": 120,
                "activity_level": 2,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            },
            {
                "timestamp": "2025-08-16T12:03:00Z",
                "heart_rate": 60,
                "activity_level": 0,
                "location": {"type": "Point", "coordinates": [-74.006 + 0.003, 40.7128]}  # Distance ~0.003
            }
        ]
        
        # Test just below distance threshold (should detect)
        with patch.object(self.interpreter.config, 'get_threshold', return_value=0.002):
            result = self.interpreter.analyze_timeline(base_data)
            fetch_events = [e for e in result if e.get("behavior") == "Playing Fetch"]
            self.assertEqual(len(fetch_events), 1, "Should detect fetch when distance > threshold")
        
        # Test just above distance threshold (should not detect)
        with patch.object(self.interpreter.config, 'get_threshold', return_value=0.004):
            result = self.interpreter.analyze_timeline(base_data)
            fetch_events = [e for e in result if e.get("behavior") == "Playing Fetch"]
            self.assertEqual(len(fetch_events), 0, "Should not detect fetch when distance <= threshold")
    
    def test_config_environment_variable_loading(self):
        """Test that configuration correctly loads from environment variables"""
        # Test default values
        config = InterpreterConfig()
        self.assertEqual(config.deep_sleep_hr_variance_threshold, 3.0)
        self.assertEqual(config.anxious_pacing_radius_threshold, 0.0007)
        self.assertEqual(config.fetch_distance_threshold, 0.001)
        
        # Test environment variable override
        with patch.dict(os.environ, {
            'PETTY_DEEP_SLEEP_HR_VARIANCE_THRESHOLD': '5.0',
            'PETTY_ANXIOUS_PACING_RADIUS_THRESHOLD': '0.001',
            'PETTY_FETCH_DISTANCE_THRESHOLD': '0.002'
        }):
            config = InterpreterConfig()
            self.assertEqual(config.deep_sleep_hr_variance_threshold, 5.0)
            self.assertEqual(config.anxious_pacing_radius_threshold, 0.001)
            self.assertEqual(config.fetch_distance_threshold, 0.002)
    
    def test_rationale_logging_exclusion_from_api(self):
        """Test that rationale is logged but excluded from API response"""
        # Create data that should trigger deep sleep detection
        test_data = [
            {
                "timestamp": f"2025-08-16T12:{i:02d}:00Z",
                "heart_rate": 50,  # Low and stable HR
                "activity_level": 0,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            }
            for i in range(5)
        ]
        
        # Mock logger to capture debug calls
        with patch.object(self.interpreter.logger, 'debug') as mock_debug:
            result = self.interpreter.analyze_timeline(test_data)
            
            # Verify events are returned
            deep_sleep_events = [e for e in result if e.get("behavior") == "Deep Sleep"]
            self.assertEqual(len(deep_sleep_events), 1)
            
            # Verify rationale is not in API response
            event = deep_sleep_events[0]
            self.assertNotIn("_rationale", event, "Rationale should not be in API response")
            
            # Verify rationale was logged internally
            mock_debug.assert_called()
            debug_calls = [call for call in mock_debug.call_args_list if "Deep sleep detected" in str(call)]
            self.assertTrue(len(debug_calls) > 0, "Rationale should be logged internally")


if __name__ == '__main__':
    unittest.main()