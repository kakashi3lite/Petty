"""
Configuration module for behavioral interpreter with SAFE_MODE support.
Implements automated canary mitigation and safe-mode controls.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SafeModeLevel(Enum):
    """Safe mode levels for system operation"""
    NORMAL = "normal"
    ELEVATED = "elevated"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class SafeModeConfig:
    """Configuration for safe mode operation"""
    level: SafeModeLevel
    rate_limit_multiplier: float
    max_concurrent_requests: int
    enable_heavy_route_throttling: bool
    github_issue_creation: bool
    alert_escalation_enabled: bool


class BehavioralInterpreterConfig:
    """Configuration manager for behavioral interpreter with safe mode support"""
    
    def __init__(self):
        self.logger = logger
        self._safe_mode = self._get_safe_mode_from_env()
        self._config_cache: Dict[str, Any] = {}
        
    def _get_safe_mode_from_env(self) -> SafeModeLevel:
        """Read SAFE_MODE flag from environment variables"""
        safe_mode_str = os.getenv("SAFE_MODE", "normal").lower()
        
        try:
            return SafeModeLevel(safe_mode_str)
        except ValueError:
            self.logger.warning(
                f"Invalid SAFE_MODE value: {safe_mode_str}, defaulting to normal"
            )
            return SafeModeLevel.NORMAL
    
    @property
    def safe_mode(self) -> SafeModeLevel:
        """Get current safe mode level"""
        return self._safe_mode
    
    def set_safe_mode(self, level: SafeModeLevel) -> None:
        """Set safe mode level"""
        self.logger.info(f"Setting safe mode to: {level.value}")
        self._safe_mode = level
        
        # Set environment variable for other processes
        os.environ["SAFE_MODE"] = level.value
        
        # Clear config cache to force recalculation
        self._config_cache.clear()
    
    def get_safe_mode_config(self) -> SafeModeConfig:
        """Get configuration based on current safe mode level"""
        cache_key = f"safe_mode_config_{self._safe_mode.value}"
        
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        config = self._build_safe_mode_config()
        self._config_cache[cache_key] = config
        return config
    
    def _build_safe_mode_config(self) -> SafeModeConfig:
        """Build safe mode configuration based on current level"""
        if self._safe_mode == SafeModeLevel.NORMAL:
            return SafeModeConfig(
                level=self._safe_mode,
                rate_limit_multiplier=1.0,
                max_concurrent_requests=100,
                enable_heavy_route_throttling=False,
                github_issue_creation=False,
                alert_escalation_enabled=False
            )
        elif self._safe_mode == SafeModeLevel.ELEVATED:
            return SafeModeConfig(
                level=self._safe_mode,
                rate_limit_multiplier=0.7,
                max_concurrent_requests=70,
                enable_heavy_route_throttling=True,
                github_issue_creation=True,
                alert_escalation_enabled=True
            )
        elif self._safe_mode == SafeModeLevel.CRITICAL:
            return SafeModeConfig(
                level=self._safe_mode,
                rate_limit_multiplier=0.3,
                max_concurrent_requests=30,
                enable_heavy_route_throttling=True,
                github_issue_creation=True,
                alert_escalation_enabled=True
            )
        else:  # EMERGENCY
            return SafeModeConfig(
                level=self._safe_mode,
                rate_limit_multiplier=0.1,
                max_concurrent_requests=10,
                enable_heavy_route_throttling=True,
                github_issue_creation=True,
                alert_escalation_enabled=True
            )
    
    def should_throttle_heavy_routes(self) -> bool:
        """Check if heavy routes should be throttled"""
        config = self.get_safe_mode_config()
        return config.enable_heavy_route_throttling
    
    def get_rate_limit_multiplier(self) -> float:
        """Get rate limit multiplier for current safe mode"""
        config = self.get_safe_mode_config()
        return config.rate_limit_multiplier
    
    def get_max_concurrent_requests(self) -> int:
        """Get maximum concurrent requests for current safe mode"""
        config = self.get_safe_mode_config()
        return config.max_concurrent_requests
    
    def should_create_github_issue(self) -> bool:
        """Check if GitHub issues should be created for incidents"""
        config = self.get_safe_mode_config()
        return config.github_issue_creation
    
    def is_alert_escalation_enabled(self) -> bool:
        """Check if alert escalation is enabled"""
        config = self.get_safe_mode_config()
        return config.alert_escalation_enabled


# Global configuration instance
config = BehavioralInterpreterConfig()


def get_config() -> BehavioralInterpreterConfig:
    """Get the global configuration instance"""
    return config


def is_safe_mode_active() -> bool:
    """Check if any safe mode is active (not normal)"""
    return config.safe_mode != SafeModeLevel.NORMAL


def get_throttling_response() -> Dict[str, Any]:
    """Get standardized 429 throttling response"""
    config_obj = config.get_safe_mode_config()
    
    return {
        "statusCode": 429,
        "headers": {
            "Content-Type": "application/json",
            "Retry-After": "60",
            "X-Safe-Mode": config_obj.level.value,
            "X-Rate-Limit-Reason": "safe-mode-throttling"
        },
        "body": {
            "error": "Service temporarily throttled",
            "message": f"System is in {config_obj.level.value} safe mode. Please try again later.",
            "safe_mode": config_obj.level.value,
            "retry_after": 60
        }
    }