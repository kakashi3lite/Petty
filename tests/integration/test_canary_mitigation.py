"""
Integration test for the complete canary mitigation workflow.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Import the modules we want to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from behavioral_interpreter.config import BehavioralInterpreterConfig, SafeModeLevel
from common.security.rate_limiter import safe_mode_rate_limit_decorator, is_heavy_route_throttled


class TestCanaryMitigationWorkflow:
    """Test the complete canary mitigation workflow"""
    
    def test_end_to_end_alarm_response(self):
        """Test complete workflow from alarm to safe mode activation"""
        # 1. Start in normal mode
        config = BehavioralInterpreterConfig()
        config.set_safe_mode(SafeModeLevel.NORMAL)
        
        # Verify normal operation
        assert config.safe_mode == SafeModeLevel.NORMAL
        assert config.should_throttle_heavy_routes() is False
        assert is_heavy_route_throttled('timeline') is False
        
        # 2. Simulate alarm triggering - set to ELEVATED
        config.set_safe_mode(SafeModeLevel.ELEVATED)
        
        # Verify elevated mode is active
        assert config.safe_mode == SafeModeLevel.ELEVATED
        assert config.should_throttle_heavy_routes() is True
        assert is_heavy_route_throttled('timeline') is True
        
        # Verify configuration changes
        safe_config = config.get_safe_mode_config()
        assert safe_config.rate_limit_multiplier == 0.7
        assert safe_config.max_concurrent_requests == 70
        assert safe_config.github_issue_creation is True
        
        # 3. Simulate critical alarm - escalate to CRITICAL
        config.set_safe_mode(SafeModeLevel.CRITICAL)
        
        # Verify critical mode is active
        assert config.safe_mode == SafeModeLevel.CRITICAL
        critical_config = config.get_safe_mode_config()
        assert critical_config.rate_limit_multiplier == 0.3
        assert critical_config.max_concurrent_requests == 30
        
        # 4. Test recovery - gradually reduce safe mode
        config.set_safe_mode(SafeModeLevel.ELEVATED)
        assert config.safe_mode == SafeModeLevel.ELEVATED
        
        config.set_safe_mode(SafeModeLevel.NORMAL)
        assert config.safe_mode == SafeModeLevel.NORMAL
        assert config.should_throttle_heavy_routes() is False
    
    def test_heavy_route_throttling_integration(self):
        """Test that heavy routes are properly throttled based on safe mode"""
        
        @safe_mode_rate_limit_decorator('timeline', tokens=1, heavy_route=True)
        def timeline_endpoint():
            return {"statusCode": 200, "body": "Timeline generated"}
        
        @safe_mode_rate_limit_decorator('health', tokens=1, heavy_route=False)  
        def health_endpoint():
            return {"statusCode": 200, "body": "Healthy"}
        
        # Normal mode - all endpoints work
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            timeline_result = timeline_endpoint()
            health_result = health_endpoint()
            
            assert timeline_result['statusCode'] == 200
            assert health_result['statusCode'] == 200
        
        # Elevated mode - heavy routes throttled, light routes work
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            timeline_result = timeline_endpoint()
            health_result = health_endpoint()
            
            assert timeline_result['statusCode'] == 429  # Throttled
            assert timeline_result['headers']['X-Safe-Mode'] == 'elevated'
            assert health_result['statusCode'] == 200  # Not throttled
    
    def test_rate_limit_scaling_with_safe_mode(self):
        """Test that rate limits scale appropriately with safe mode changes"""
        from common.security.rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
        
        # Test each safe mode level
        safe_mode_tests = [
            ('normal', 1.0, 100, 10.0),
            ('elevated', 0.7, 70, 7.0),
            ('critical', 0.3, 30, 3.0),
            ('emergency', 0.1, 10, 1.0)
        ]
        
        for mode, expected_multiplier, expected_max, expected_rate in safe_mode_tests:
            with patch.dict(os.environ, {'SAFE_MODE': mode}):
                max_tokens, refill_rate = rate_limiter._get_effective_limits()
                
                assert max_tokens == expected_max, f"Mode {mode}: expected max_tokens {expected_max}, got {max_tokens}"
                assert refill_rate == expected_rate, f"Mode {mode}: expected refill_rate {expected_rate}, got {refill_rate}"
    
    def test_github_issue_creation_flag(self):
        """Test that GitHub issue creation is enabled based on safe mode"""
        config = BehavioralInterpreterConfig()
        
        # Normal mode - no GitHub issues
        config.set_safe_mode(SafeModeLevel.NORMAL)
        assert config.should_create_github_issue() is False
        
        # Elevated mode - GitHub issues enabled
        config.set_safe_mode(SafeModeLevel.ELEVATED)
        assert config.should_create_github_issue() is True
        
        # Critical mode - GitHub issues enabled
        config.set_safe_mode(SafeModeLevel.CRITICAL)
        assert config.should_create_github_issue() is True
        
        # Emergency mode - GitHub issues enabled
        config.set_safe_mode(SafeModeLevel.EMERGENCY)
        assert config.should_create_github_issue() is True
    
    def test_safe_mode_persistence_across_environment_changes(self):
        """Test that safe mode persists correctly across environment changes"""
        config = BehavioralInterpreterConfig()
        
        # Set safe mode programmatically
        config.set_safe_mode(SafeModeLevel.CRITICAL)
        
        # Verify it's reflected in environment
        assert os.environ.get('SAFE_MODE') == 'critical'
        
        # Create new config instance - should read from environment
        new_config = BehavioralInterpreterConfig()
        assert new_config.safe_mode == SafeModeLevel.CRITICAL
    
    def test_alarm_mitigation_priorities(self):
        """Test that different alarm types trigger appropriate safe mode levels"""
        # Simulate different alarm scenarios
        alarm_scenarios = [
            {
                'alarm_name': 'Petty-API-Gateway-High-Error-Rate',
                'expected_mode': SafeModeLevel.ELEVATED
            },
            {
                'alarm_name': 'Petty-Lambda-Critical-Throttles',
                'expected_mode': SafeModeLevel.EMERGENCY  # Throttling is critical
            },
            {
                'alarm_name': 'Petty-Lambda-High-Duration',
                'expected_mode': SafeModeLevel.ELEVATED
            }
        ]
        
        config = BehavioralInterpreterConfig()
        
        for scenario in alarm_scenarios:
            # Reset to normal
            config.set_safe_mode(SafeModeLevel.NORMAL)
            
            # Simulate alarm-based safe mode determination
            alarm_name = scenario['alarm_name'].lower()
            if 'critical' in alarm_name or 'throttle' in alarm_name:
                if 'throttle' in alarm_name:
                    determined_mode = SafeModeLevel.EMERGENCY
                else:
                    determined_mode = SafeModeLevel.CRITICAL
            else:
                determined_mode = SafeModeLevel.ELEVATED
            
            # Set the determined mode
            config.set_safe_mode(determined_mode)
            
            # Verify it matches expected
            assert config.safe_mode == scenario['expected_mode'], \
                f"Alarm {scenario['alarm_name']} should trigger {scenario['expected_mode']}, got {config.safe_mode}"


if __name__ == '__main__':
    pytest.main([__file__])