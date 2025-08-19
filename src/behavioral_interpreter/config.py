"""
Configuration management for behavioral interpreter with safety bounds and versioning.
Supports auto-tuning while enforcing safety constraints.
"""

from typing import Dict, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from datetime import datetime, timezone

# Version tracking for config changes
CONFIG_VERSION = "1.0.0"

class BehaviorConfigType(Enum):
    """Types of behavior configurations"""
    DEEP_SLEEP = "deep_sleep"
    ANXIOUS_PACING = "anxious_pacing"
    PLAYING_FETCH = "playing_fetch"

@dataclass
class ThresholdBounds:
    """Safety bounds for threshold values"""
    min_value: float
    max_value: float
    default_value: float
    
    def clamp(self, value: float) -> float:
        """Clamp value to bounds"""
        return max(self.min_value, min(self.max_value, value))

@dataclass
class BehaviorConfig:
    """Configuration for a single behavior type with safety bounds"""
    name: str
    min_data_points: int
    confidence_threshold: float
    activity_levels: list
    heart_rate_range: Tuple[int, int]
    description: str
    
    # Safety bounds for auto-tuning
    confidence_bounds: ThresholdBounds
    min_data_points_bounds: ThresholdBounds
    heart_rate_bounds: Tuple[ThresholdBounds, ThresholdBounds]  # (min_hr_bounds, max_hr_bounds)
    
    def apply_safety_bounds(self) -> 'BehaviorConfig':
        """Apply safety bounds to current values"""
        clamped_config = BehaviorConfig(
            name=self.name,
            min_data_points=int(self.min_data_points_bounds.clamp(self.min_data_points)),
            confidence_threshold=self.confidence_bounds.clamp(self.confidence_threshold),
            activity_levels=self.activity_levels.copy(),
            heart_rate_range=(
                int(self.heart_rate_bounds[0].clamp(self.heart_rate_range[0])),
                int(self.heart_rate_bounds[1].clamp(self.heart_rate_range[1]))
            ),
            description=self.description,
            confidence_bounds=self.confidence_bounds,
            min_data_points_bounds=self.min_data_points_bounds,
            heart_rate_bounds=self.heart_rate_bounds
        )
        return clamped_config

class BehavioralInterpreterConfig:
    """Centralized configuration management for behavioral interpreter"""
    
    def __init__(self, config_version: str = CONFIG_VERSION):
        self.config_version = config_version
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self._configs = self._load_default_configs()
    
    def _load_default_configs(self) -> Dict[str, BehaviorConfig]:
        """Load default behavior configurations with safety bounds"""
        return {
            BehaviorConfigType.DEEP_SLEEP.value: BehaviorConfig(
                name="Deep Sleep",
                min_data_points=4,
                confidence_threshold=0.9,
                activity_levels=[0],
                heart_rate_range=(40, 65),
                description="Extended period of minimal activity with stable, low heart rate",
                
                # Safety bounds for auto-tuning
                confidence_bounds=ThresholdBounds(min_value=0.7, max_value=0.99, default_value=0.9),
                min_data_points_bounds=ThresholdBounds(min_value=3, max_value=10, default_value=4),
                heart_rate_bounds=(
                    ThresholdBounds(min_value=35, max_value=50, default_value=40),  # min HR
                    ThresholdBounds(min_value=55, max_value=80, default_value=65)   # max HR
                )
            ),
            
            BehaviorConfigType.ANXIOUS_PACING.value: BehaviorConfig(
                name="Anxious Pacing",
                min_data_points=6,
                confidence_threshold=0.75,
                activity_levels=[1],
                heart_rate_range=(70, 110),
                description="Repetitive movement in small area with elevated heart rate",
                
                # Safety bounds for auto-tuning
                confidence_bounds=ThresholdBounds(min_value=0.6, max_value=0.95, default_value=0.75),
                min_data_points_bounds=ThresholdBounds(min_value=4, max_value=12, default_value=6),
                heart_rate_bounds=(
                    ThresholdBounds(min_value=60, max_value=80, default_value=70),   # min HR
                    ThresholdBounds(min_value=100, max_value=130, default_value=110) # max HR
                )
            ),
            
            BehaviorConfigType.PLAYING_FETCH.value: BehaviorConfig(
                name="Playing Fetch",
                min_data_points=4,
                confidence_threshold=0.8,
                activity_levels=[0, 2],
                heart_rate_range=(80, 160),
                description="High activity followed by rest with significant location changes",
                
                # Safety bounds for auto-tuning
                confidence_bounds=ThresholdBounds(min_value=0.65, max_value=0.95, default_value=0.8),
                min_data_points_bounds=ThresholdBounds(min_value=3, max_value=8, default_value=4),
                heart_rate_bounds=(
                    ThresholdBounds(min_value=70, max_value=90, default_value=80),   # min HR
                    ThresholdBounds(min_value=140, max_value=180, default_value=160) # max HR
                )
            )
        }
    
    def get_config(self, behavior_type: str) -> Optional[BehaviorConfig]:
        """Get configuration for a behavior type"""
        return self._configs.get(behavior_type)
    
    def get_all_configs(self) -> Dict[str, BehaviorConfig]:
        """Get all behavior configurations"""
        return self._configs.copy()
    
    def update_config(self, behavior_type: str, new_config: BehaviorConfig) -> bool:
        """Update configuration with safety bounds enforcement"""
        if behavior_type not in self._configs:
            return False
        
        # Apply safety bounds before updating
        safe_config = new_config.apply_safety_bounds()
        self._configs[behavior_type] = safe_config
        self.last_updated = datetime.now(timezone.utc).isoformat()
        return True
    
    def update_thresholds(self, behavior_type: str, 
                         confidence_threshold: Optional[float] = None,
                         min_data_points: Optional[int] = None,
                         heart_rate_range: Optional[Tuple[int, int]] = None) -> bool:
        """Update specific thresholds for a behavior type"""
        config = self.get_config(behavior_type)
        if not config:
            return False
        
        # Update only provided values
        if confidence_threshold is not None:
            config.confidence_threshold = confidence_threshold
        if min_data_points is not None:
            config.min_data_points = min_data_points
        if heart_rate_range is not None:
            config.heart_rate_range = heart_rate_range
        
        # Apply safety bounds and update
        return self.update_config(behavior_type, config)
    
    def reset_to_defaults(self, behavior_type: Optional[str] = None):
        """Reset configuration(s) to defaults"""
        if behavior_type:
            if behavior_type in self._configs:
                # Reset specific config to defaults
                default_configs = self._load_default_configs()
                self._configs[behavior_type] = default_configs[behavior_type]
        else:
            # Reset all configs to defaults
            self._configs = self._load_default_configs()
        
        self.last_updated = datetime.now(timezone.utc).isoformat()
    
    def validate_config_integrity(self) -> Dict[str, list]:
        """Validate all configurations meet safety requirements"""
        issues = {}
        
        for behavior_type, config in self._configs.items():
            config_issues = []
            
            # Check confidence threshold bounds
            if not (config.confidence_bounds.min_value <= config.confidence_threshold <= config.confidence_bounds.max_value):
                config_issues.append(f"Confidence threshold {config.confidence_threshold} out of bounds [{config.confidence_bounds.min_value}, {config.confidence_bounds.max_value}]")
            
            # Check min data points bounds
            if not (config.min_data_points_bounds.min_value <= config.min_data_points <= config.min_data_points_bounds.max_value):
                config_issues.append(f"Min data points {config.min_data_points} out of bounds [{config.min_data_points_bounds.min_value}, {config.min_data_points_bounds.max_value}]")
            
            # Check heart rate bounds
            min_hr, max_hr = config.heart_rate_range
            if not (config.heart_rate_bounds[0].min_value <= min_hr <= config.heart_rate_bounds[0].max_value):
                config_issues.append(f"Min heart rate {min_hr} out of bounds [{config.heart_rate_bounds[0].min_value}, {config.heart_rate_bounds[0].max_value}]")
            if not (config.heart_rate_bounds[1].min_value <= max_hr <= config.heart_rate_bounds[1].max_value):
                config_issues.append(f"Max heart rate {max_hr} out of bounds [{config.heart_rate_bounds[1].min_value}, {config.heart_rate_bounds[1].max_value}]")
            
            # Check logical consistency
            if min_hr >= max_hr:
                config_issues.append(f"Min heart rate {min_hr} >= max heart rate {max_hr}")
            
            if config_issues:
                issues[behavior_type] = config_issues
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary"""
        return {
            "config_version": self.config_version,
            "last_updated": self.last_updated,
            "behaviors": {
                behavior_type: {
                    "name": config.name,
                    "min_data_points": config.min_data_points,
                    "confidence_threshold": config.confidence_threshold,
                    "activity_levels": config.activity_levels,
                    "heart_rate_range": config.heart_rate_range,
                    "description": config.description,
                    "safety_bounds": {
                        "confidence_bounds": asdict(config.confidence_bounds),
                        "min_data_points_bounds": asdict(config.min_data_points_bounds),
                        "heart_rate_bounds": [asdict(config.heart_rate_bounds[0]), asdict(config.heart_rate_bounds[1])]
                    }
                }
                for behavior_type, config in self._configs.items()
            }
        }
    
    def to_json(self) -> str:
        """Export configuration to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    def save_to_file(self, filepath: str):
        """Save configuration to file"""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehavioralInterpreterConfig':
        """Load configuration from dictionary"""
        config = cls(config_version=data.get("config_version", CONFIG_VERSION))
        config.last_updated = data.get("last_updated", config.last_updated)
        
        # Load behavior configs
        if "behaviors" in data:
            for behavior_type, behavior_data in data["behaviors"].items():
                bounds_data = behavior_data.get("safety_bounds", {})
                
                behavior_config = BehaviorConfig(
                    name=behavior_data["name"],
                    min_data_points=behavior_data["min_data_points"],
                    confidence_threshold=behavior_data["confidence_threshold"],
                    activity_levels=behavior_data["activity_levels"],
                    heart_rate_range=tuple(behavior_data["heart_rate_range"]),
                    description=behavior_data["description"],
                    confidence_bounds=ThresholdBounds(**bounds_data.get("confidence_bounds", {})),
                    min_data_points_bounds=ThresholdBounds(**bounds_data.get("min_data_points_bounds", {})),
                    heart_rate_bounds=(
                        ThresholdBounds(**bounds_data.get("heart_rate_bounds", [{}])[0]),
                        ThresholdBounds(**bounds_data.get("heart_rate_bounds", [{}, {}])[1])
                    )
                )
                config._configs[behavior_type] = behavior_config
        
        return config
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BehavioralInterpreterConfig':
        """Load configuration from JSON string"""
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'BehavioralInterpreterConfig':
        """Load configuration from file"""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())

# Global configuration instance
_global_config: Optional[BehavioralInterpreterConfig] = None

def get_global_config() -> BehavioralInterpreterConfig:
    """Get or create global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = BehavioralInterpreterConfig()
    return _global_config

def load_config_from_env() -> BehavioralInterpreterConfig:
    """Load configuration from environment variable or file"""
    config_path = os.getenv("BEHAVIORAL_CONFIG_PATH")
    config_json = os.getenv("BEHAVIORAL_CONFIG_JSON")
    
    if config_json:
        return BehavioralInterpreterConfig.from_json(config_json)
    elif config_path and os.path.exists(config_path):
        return BehavioralInterpreterConfig.load_from_file(config_path)
    else:
        return BehavioralInterpreterConfig()