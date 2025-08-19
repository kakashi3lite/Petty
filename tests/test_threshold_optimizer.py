"""
Unit tests for threshold optimizer with dry-run mode testing.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add tools and src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from optimize_thresholds import ThresholdOptimizer
from behavioral_interpreter.config import BehavioralInterpreterConfig, BehaviorConfigType

class TestThresholdOptimizer(unittest.TestCase):
    """Test cases for ThresholdOptimizer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_bucket = "test-bucket"
        self.optimizer = ThresholdOptimizer(
            s3_bucket=self.test_bucket,
            dry_run=True
        )
        
        # Mock feedback data
        self.sample_feedback = [
            {
                "event_id": "test_001",
                "collar_id": "SN-12345",
                "user_feedback": "correct",
                "ts": 1692172800,
                "segment": {
                    "collar_data": [
                        {
                            "timestamp": "2025-08-16T12:00:00Z",
                            "heart_rate": 45,
                            "activity_level": 0,
                            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
                        },
                        {
                            "timestamp": "2025-08-16T12:01:00Z",
                            "heart_rate": 44,
                            "activity_level": 0,
                            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
                        }
                    ]
                }
            },
            {
                "event_id": "test_002",
                "collar_id": "SN-12345",
                "user_feedback": "incorrect",
                "ts": 1692172900,
                "segment": {
                    "collar_data": [
                        {
                            "timestamp": "2025-08-16T12:05:00Z",
                            "heart_rate": 120,
                            "activity_level": 2,
                            "location": {"type": "Point", "coordinates": [-74.007, 40.7129]}
                        }
                    ]
                }
            }
        ]
    
    def test_validate_feedback_item_valid(self):
        """Test validation of valid feedback item"""
        valid_item = {
            "event_id": "test_001",
            "collar_id": "SN-12345",
            "user_feedback": "correct",
            "ts": 1692172800
        }
        self.assertTrue(self.optimizer._validate_feedback_item(valid_item))
    
    def test_validate_feedback_item_invalid(self):
        """Test validation of invalid feedback items"""
        # Missing required field
        invalid_item1 = {
            "event_id": "test_001",
            "collar_id": "SN-12345",
            "ts": 1692172800
        }
        self.assertFalse(self.optimizer._validate_feedback_item(invalid_item1))
        
        # Invalid feedback value
        invalid_item2 = {
            "event_id": "test_001",
            "collar_id": "SN-12345",
            "user_feedback": "maybe",
            "ts": 1692172800
        }
        self.assertFalse(self.optimizer._validate_feedback_item(invalid_item2))
    
    def test_prepare_training_data(self):
        """Test preparation of training data from feedback"""
        self.optimizer.feedback_data = self.sample_feedback
        training_data = self.optimizer.prepare_training_data()
        
        self.assertEqual(len(training_data), 2)
        
        # Check first sample (correct feedback -> label 1)
        collar_data1, label1 = training_data[0]
        self.assertEqual(label1, 1)
        self.assertEqual(len(collar_data1), 2)
        
        # Check second sample (incorrect feedback -> label 0)
        collar_data2, label2 = training_data[1]
        self.assertEqual(label2, 0)
        self.assertEqual(len(collar_data2), 1)
    
    def test_evaluate_thresholds_minimal_data(self):
        """Test threshold evaluation with minimal data"""
        # Test with insufficient data
        training_data = [([], 1), ([], 0)]  # Only 2 samples
        
        f1_score = self.optimizer.evaluate_thresholds(
            behavior_type=BehaviorConfigType.DEEP_SLEEP.value,
            confidence_threshold=0.9,
            min_data_points=4,
            min_hr=40,
            max_hr=65,
            training_data=training_data
        )
        
        self.assertEqual(f1_score, 0.0)  # Should return 0 for insufficient data
    
    @patch('optimize_thresholds.gp_minimize')
    def test_optimize_behavior_thresholds_dry_run(self, mock_gp_minimize):
        """Test behavior threshold optimization in dry-run mode"""
        # Mock the optimization result
        mock_result = MagicMock()
        mock_result.x = [0.85, 5, 42, 63]  # optimal parameters
        mock_result.fun = -0.75  # negative F1 score
        mock_result.func_vals = [-0.1, -0.3, -0.5, -0.7, -0.75]
        mock_gp_minimize.return_value = mock_result
        
        # Create some training data
        training_data = self._create_mock_training_data(20)
        
        result = self.optimizer.optimize_behavior_thresholds(
            behavior_type=BehaviorConfigType.DEEP_SLEEP.value,
            training_data=training_data,
            n_calls=5
        )
        
        # Check result structure
        self.assertIn('confidence_threshold', result)
        self.assertIn('min_data_points', result)
        self.assertIn('min_hr', result)
        self.assertIn('max_hr', result)
        self.assertIn('f1_score', result)
        
        # Check values are within expected ranges
        self.assertEqual(result['confidence_threshold'], 0.85)
        self.assertEqual(result['min_data_points'], 5)
        self.assertEqual(result['min_hr'], 42)
        self.assertEqual(result['max_hr'], 63)
        self.assertEqual(result['f1_score'], 0.75)
    
    def test_apply_optimized_thresholds_dry_run(self):
        """Test applying optimized thresholds in dry-run mode"""
        optimization_results = {
            BehaviorConfigType.DEEP_SLEEP.value: {
                'confidence_threshold': 0.85,
                'min_data_points': 5,
                'min_hr': 42,
                'max_hr': 63,
                'f1_score': 0.75
            }
        }
        
        applied_changes = self.optimizer.apply_optimized_thresholds(
            optimization_results,
            min_improvement_threshold=0.1
        )
        
        # In dry-run mode, should indicate changes would be applied
        self.assertTrue(applied_changes[BehaviorConfigType.DEEP_SLEEP.value])
    
    def test_apply_optimized_thresholds_insufficient_improvement(self):
        """Test skipping optimization with insufficient improvement"""
        optimization_results = {
            BehaviorConfigType.DEEP_SLEEP.value: {
                'confidence_threshold': 0.85,
                'min_data_points': 5,
                'min_hr': 42,
                'max_hr': 63,
                'f1_score': 0.02  # Below threshold
            }
        }
        
        applied_changes = self.optimizer.apply_optimized_thresholds(
            optimization_results,
            min_improvement_threshold=0.05
        )
        
        # Should not apply changes due to insufficient improvement
        self.assertFalse(applied_changes[BehaviorConfigType.DEEP_SLEEP.value])
    
    def test_generate_optimization_report(self):
        """Test optimization report generation"""
        optimization_results = {
            BehaviorConfigType.DEEP_SLEEP.value: {
                'confidence_threshold': 0.85,
                'f1_score': 0.75
            },
            BehaviorConfigType.ANXIOUS_PACING.value: {
                'error': 'Insufficient data'
            }
        }
        
        applied_changes = {
            BehaviorConfigType.DEEP_SLEEP.value: True,
            BehaviorConfigType.ANXIOUS_PACING.value: False
        }
        
        self.optimizer.feedback_data = self.sample_feedback
        
        report = self.optimizer.generate_optimization_report(
            optimization_results, applied_changes
        )
        
        # Check report structure
        self.assertIn('timestamp', report)
        self.assertIn('config_version', report)
        self.assertIn('dry_run', report)
        self.assertIn('feedback_data_count', report)
        self.assertIn('optimization_results', report)
        self.assertIn('applied_changes', report)
        self.assertIn('summary', report)
        
        # Check summary
        summary = report['summary']
        self.assertEqual(summary['total_behaviors'], 2)
        self.assertEqual(summary['successful_optimizations'], 1)
        self.assertEqual(summary['applied_changes_count'], 1)
    
    @patch('optimize_thresholds.boto3.client')
    def test_load_feedback_data_empty_bucket(self, mock_boto_client):
        """Test loading feedback data from empty S3 bucket"""
        # Create a new optimizer instance with mocked S3
        optimizer = ThresholdOptimizer(
            s3_bucket=self.test_bucket,
            dry_run=True
        )
        
        # Mock empty S3 response
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        optimizer.s3_client = mock_s3
        
        mock_paginator = MagicMock()
        mock_s3.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{}]  # Empty page
        
        count = optimizer.load_feedback_data()
        self.assertEqual(count, 0)
        self.assertEqual(len(optimizer.feedback_data), 0)
    
    @patch('optimize_thresholds.boto3.client')
    def test_load_feedback_data_with_content(self, mock_boto_client):
        """Test loading feedback data with content"""
        # Create a new optimizer instance with mocked S3
        optimizer = ThresholdOptimizer(
            s3_bucket=self.test_bucket,
            dry_run=True
        )
        
        # Mock S3 responses
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        optimizer.s3_client = mock_s3
        
        mock_paginator = MagicMock()
        mock_s3.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{
            'Contents': [
                {'Key': 'feedback/test1.json'},
                {'Key': 'feedback/test2.json'}
            ]
        }]
        
        # Mock S3 object responses
        mock_s3.get_object.side_effect = [
            {'Body': MagicMock(read=lambda: json.dumps(self.sample_feedback[0]).encode())},
            {'Body': MagicMock(read=lambda: json.dumps(self.sample_feedback[1]).encode())}
        ]
        
        count = optimizer.load_feedback_data()
        self.assertEqual(count, 2)
        self.assertEqual(len(optimizer.feedback_data), 2)
    
    def test_config_safety_bounds_enforcement(self):
        """Test that configuration safety bounds are enforced"""
        config = BehavioralInterpreterConfig()
        
        # Test updating with values outside bounds
        behavior_type = BehaviorConfigType.DEEP_SLEEP.value
        
        # Try to set confidence threshold above max bound
        success = config.update_thresholds(
            behavior_type,
            confidence_threshold=1.5,  # Above max bound
            min_data_points=2,         # Below min bound
            heart_rate_range=(20, 200) # Outside bounds
        )
        
        self.assertTrue(success)  # Update should succeed but values should be clamped
        
        updated_config = config.get_config(behavior_type)
        
        # Values should be clamped to bounds
        self.assertLessEqual(updated_config.confidence_threshold, 
                           updated_config.confidence_bounds.max_value)
        self.assertGreaterEqual(updated_config.min_data_points,
                              updated_config.min_data_points_bounds.min_value)
    
    def _create_mock_training_data(self, count: int):
        """Create mock training data for testing"""
        training_data = []
        for i in range(count):
            collar_data = [{
                "timestamp": f"2025-08-16T12:{i:02d}:00Z",
                "heart_rate": 50 + (i % 20),
                "activity_level": i % 3,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            }]
            label = i % 2  # Alternate between 0 and 1
            training_data.append((collar_data, label))
        return training_data

class TestConfigModule(unittest.TestCase):
    """Test cases for configuration module"""
    
    def test_config_serialization(self):
        """Test configuration serialization and deserialization"""
        config = BehavioralInterpreterConfig()
        
        # Serialize to dict
        config_dict = config.to_dict()
        self.assertIn('config_version', config_dict)
        self.assertIn('behaviors', config_dict)
        
        # Deserialize from dict
        loaded_config = BehavioralInterpreterConfig.from_dict(config_dict)
        self.assertEqual(loaded_config.config_version, config.config_version)
        
        # Check behavior configs match
        original_behaviors = config.get_all_configs()
        loaded_behaviors = loaded_config.get_all_configs()
        self.assertEqual(len(original_behaviors), len(loaded_behaviors))
    
    def test_config_file_operations(self):
        """Test saving and loading configuration from file"""
        config = BehavioralInterpreterConfig()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            config.save_to_file(f.name)
            
            # Load from file
            loaded_config = BehavioralInterpreterConfig.load_from_file(f.name)
            self.assertEqual(loaded_config.config_version, config.config_version)
            
            # Clean up
            os.unlink(f.name)
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = BehavioralInterpreterConfig()
        
        # Valid configuration should have no issues
        issues = config.validate_config_integrity()
        self.assertEqual(len(issues), 0)
        
        # Manually break a configuration
        deep_sleep_config = config.get_config(BehaviorConfigType.DEEP_SLEEP.value)
        deep_sleep_config.confidence_threshold = 1.5  # Invalid value
        
        issues = config.validate_config_integrity()
        self.assertGreater(len(issues), 0)
        self.assertIn(BehaviorConfigType.DEEP_SLEEP.value, issues)

if __name__ == '__main__':
    unittest.main()