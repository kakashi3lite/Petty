"""
Configuration management for behavioral interpreter thresholds.
Supports environment variables with sane defaults.
"""

import os
from typing import Dict, Any


class InterpreterConfig:
    """Configuration class for behavioral interpreter thresholds"""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults"""
        self.deep_sleep_hr_variance_threshold = float(
            os.getenv('PETTY_DEEP_SLEEP_HR_VARIANCE_THRESHOLD', '3.0')
        )
        
        self.anxious_pacing_radius_threshold = float(
            os.getenv('PETTY_ANXIOUS_PACING_RADIUS_THRESHOLD', '0.0007')
        )
        
        self.fetch_distance_threshold = float(
            os.getenv('PETTY_FETCH_DISTANCE_THRESHOLD', '0.001')
        )
    
    def get_threshold(self, behavior_type: str, threshold_name: str) -> float:
        """Get threshold value for specific behavior and threshold type"""
        threshold_map = {
            'deep_sleep': {
                'hr_variance': self.deep_sleep_hr_variance_threshold
            },
            'anxious_pacing': {
                'radius': self.anxious_pacing_radius_threshold
            },
            'playing_fetch': {
                'distance': self.fetch_distance_threshold
            }
        }
        
        return threshold_map.get(behavior_type, {}).get(threshold_name, 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary for logging"""
        return {
            'deep_sleep_hr_variance_threshold': self.deep_sleep_hr_variance_threshold,
            'anxious_pacing_radius_threshold': self.anxious_pacing_radius_threshold,
            'fetch_distance_threshold': self.fetch_distance_threshold
        }


# Global configuration instance
config = InterpreterConfig()