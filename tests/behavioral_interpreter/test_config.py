"""
Tests for behavioral interpreter configuration and safe mode functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Import the modules we want to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from behavioral_interpreter.config import (
    BehavioralInterpreterConfig,
    SafeModeLevel,
    SafeModeConfig,
    get_config,
    is_safe_mode_active,
    get_throttling_response
)


class TestBehavioralInterpreterConfig:
    """Test safe mode configuration functionality"""
    
    def test_default_safe_mode_is_normal(self):
        """Test that default safe mode is normal"""
        with patch.dict(os.environ, {}, clear=True):
            config = BehavioralInterpreterConfig()
            assert config.safe_mode == SafeModeLevel.NORMAL
    
    def test_safe_mode_from_environment(self):
        """Test reading safe mode from environment variable"""
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            config = BehavioralInterpreterConfig()
            assert config.safe_mode == SafeModeLevel.ELEVATED
    
    def test_invalid_safe_mode_defaults_to_normal(self):
        """Test that invalid safe mode values default to normal"""
        with patch.dict(os.environ, {'SAFE_MODE': 'invalid_mode'}):
            config = BehavioralInterpreterConfig()
            assert config.safe_mode == SafeModeLevel.NORMAL
    
    def test_set_safe_mode_updates_environment(self):
        """Test that setting safe mode updates environment variable"""
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.CRITICAL)
        
        assert config.safe_mode == SafeModeLevel.CRITICAL
        assert os.environ.get('SAFE_MODE') == 'critical'
    
    def test_normal_safe_mode_config(self):
        """Test configuration for normal safe mode"""
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.NORMAL)
        
        safe_config = config.get_safe_mode_config()
        
        assert safe_config.level == SafeModeLevel.NORMAL
        assert safe_config.rate_limit_multiplier == 1.0
        assert safe_config.max_concurrent_requests == 100
        assert safe_config.enable_heavy_route_throttling is False
        assert safe_config.github_issue_creation is False
    
    def test_elevated_safe_mode_config(self):
        """Test configuration for elevated safe mode"""
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.ELEVATED)
        
        safe_config = config.get_safe_mode_config()
        
        assert safe_config.level == SafeModeLevel.ELEVATED
        assert safe_config.rate_limit_multiplier == 0.7
        assert safe_config.max_concurrent_requests == 70
        assert safe_config.enable_heavy_route_throttling is True
        assert safe_config.github_issue_creation is True
    
    def test_critical_safe_mode_config(self):
        """Test configuration for critical safe mode"""
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.CRITICAL)
        
        safe_config = config.get_safe_mode_config()
        
        assert safe_config.level == SafeModeLevel.CRITICAL
        assert safe_config.rate_limit_multiplier == 0.3
        assert safe_config.max_concurrent_requests == 30
        assert safe_config.enable_heavy_route_throttling is True
        assert safe_config.github_issue_creation is True
    
    def test_emergency_safe_mode_config(self):
        """Test configuration for emergency safe mode"""
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.EMERGENCY)
        
        safe_config = config.get_safe_mode_config()
        
        assert safe_config.level == SafeModeLevel.EMERGENCY
        assert safe_config.rate_limit_multiplier == 0.1
        assert safe_config.max_concurrent_requests == 10
        assert safe_config.enable_heavy_route_throttling is True
        assert safe_config.github_issue_creation is True
    
    def test_should_throttle_heavy_routes(self):
        """Test heavy route throttling logic"""
        config = BehavioralInterpreterConfig()
        
        # Normal mode - no throttling
        config.set_safe_mode(SafeModeLevel.NORMAL)
        assert config.should_throttle_heavy_routes() is False
        
        # Elevated mode - throttling enabled
        config.set_safe_mode(SafeModeLevel.ELEVATED)
        assert config.should_throttle_heavy_routes() is True
    
    def test_config_caching(self):
        """Test that configuration is cached properly"""
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.CRITICAL)
        
        # Get config twice
        config1 = config.get_safe_mode_config()
        config2 = config.get_safe_mode_config()
        
        # Should be the same object (cached)
        assert config1 is config2
        
        # Change safe mode should clear cache
        config.set_safe_mode(SafeModeLevel.ELEVATED)
        config3 = config.get_safe_mode_config()
        
        # Should be different object (cache cleared)
        assert config1 is not config3
        assert config3.level == SafeModeLevel.ELEVATED


class TestGlobalFunctions:
    """Test global configuration functions"""
    
    def test_get_config_returns_singleton(self):
        """Test that get_config returns the same instance"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_is_safe_mode_active(self):
        """Test safe mode active detection"""
        config = get_config()
        
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            config.set_safe_mode(SafeModeLevel.NORMAL)
            assert is_safe_mode_active() is False
        
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            config.set_safe_mode(SafeModeLevel.ELEVATED)
            assert is_safe_mode_active() is True
        
        with patch.dict(os.environ, {'SAFE_MODE': 'critical'}):
            config.set_safe_mode(SafeModeLevel.CRITICAL)
            assert is_safe_mode_active() is True
    
    def test_get_throttling_response(self):
        """Test throttling response generation"""
        config = get_config()
        
        with patch.dict(os.environ, {'SAFE_MODE': 'critical'}):
            config.set_safe_mode(SafeModeLevel.CRITICAL)
            response = get_throttling_response()
            
            assert response['statusCode'] == 429
            assert response['headers']['Content-Type'] == 'application/json'
            assert response['headers']['X-Safe-Mode'] == 'critical'
            assert 'critical' in response['body']['message']


class TestSafeModeIntegration:
    """Test integration with other system components"""
    
    def test_safe_mode_persistence_across_instances(self):
        """Test that safe mode persists across config instances"""
        # Set safe mode in one instance
        config1 = BehavioralInterpreterConfig()
        config1.set_safe_mode(SafeModeLevel.CRITICAL)
        
        # Create new instance
        config2 = BehavioralInterpreterConfig()
        
        # Should read from environment
        assert config2.safe_mode == SafeModeLevel.CRITICAL
    
    @patch('behavioral_interpreter.config.logger')
    def test_logging_on_safe_mode_change(self, mock_logger):
        """Test that safe mode changes are logged"""
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.EMERGENCY)
        
        mock_logger.info.assert_called_with("Setting safe mode to: emergency")


if __name__ == '__main__':
    pytest.main([__file__])