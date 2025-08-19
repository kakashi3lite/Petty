"""
Tests for safe mode integration with rate limiter.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Import the modules we want to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from common.security.rate_limiter import (
    RateLimiter,
    safe_mode_rate_limit_decorator,
    is_heavy_route_throttled,
    get_throttling_response,
    HEAVY_ROUTES
)


class TestSafeModeRateLimiter:
    """Test rate limiter with safe mode integration"""
    
    def test_normal_mode_no_throttling(self):
        """Test that normal mode doesn't apply throttling"""
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            rate_limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
            
            # Should get full capacity
            effective_max, effective_rate = rate_limiter._get_effective_limits()
            assert effective_max == 10
            assert effective_rate == 1.0
    
    def test_elevated_mode_throttling(self):
        """Test that elevated mode applies 30% throttling"""
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            rate_limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
            
            # Should get 70% capacity (0.7 multiplier)
            effective_max, effective_rate = rate_limiter._get_effective_limits()
            assert effective_max == 7  # 10 * 0.7
            assert effective_rate == 0.7  # 1.0 * 0.7
    
    def test_critical_mode_throttling(self):
        """Test that critical mode applies 70% throttling"""
        with patch.dict(os.environ, {'SAFE_MODE': 'critical'}):
            rate_limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
            
            # Should get 30% capacity (0.3 multiplier)
            effective_max, effective_rate = rate_limiter._get_effective_limits()
            assert effective_max == 3  # 10 * 0.3
            assert effective_rate == 0.3  # 1.0 * 0.3
    
    def test_emergency_mode_throttling(self):
        """Test that emergency mode applies 90% throttling"""
        with patch.dict(os.environ, {'SAFE_MODE': 'emergency'}):
            rate_limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
            
            # Should get 10% capacity (0.1 multiplier)
            effective_max, effective_rate = rate_limiter._get_effective_limits()
            assert effective_max == 1  # 10 * 0.1
            assert effective_rate == 0.1  # 1.0 * 0.1
    
    def test_dynamic_safe_mode_adjustment(self):
        """Test that rate limits adjust dynamically when safe mode changes"""
        rate_limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
        
        # Start in normal mode
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            bucket = rate_limiter._get_bucket('test_key')
            assert bucket['tokens'] == 10
        
        # Change to critical mode
        with patch.dict(os.environ, {'SAFE_MODE': 'critical'}):
            bucket = rate_limiter._get_bucket('test_key')
            # Bucket should be refilled with new limits
            assert bucket['tokens'] <= 3  # New limit is 3


class TestHeavyRouteThrottling:
    """Test heavy route throttling functionality"""
    
    def test_heavy_routes_definition(self):
        """Test that heavy routes are properly defined"""
        expected_heavy_routes = {'timeline', 'ingest', 'feedback'}
        assert HEAVY_ROUTES == expected_heavy_routes
    
    def test_heavy_route_throttling_normal_mode(self):
        """Test that heavy routes are not throttled in normal mode"""
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            assert is_heavy_route_throttled('timeline') is False
            assert is_heavy_route_throttled('ingest') is False
            assert is_heavy_route_throttled('feedback') is False
    
    def test_heavy_route_throttling_elevated_mode(self):
        """Test that heavy routes are throttled in elevated mode"""
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            assert is_heavy_route_throttled('timeline') is True
            assert is_heavy_route_throttled('ingest') is True
            assert is_heavy_route_throttled('feedback') is True
    
    def test_non_heavy_route_not_throttled(self):
        """Test that non-heavy routes are not throttled"""
        with patch.dict(os.environ, {'SAFE_MODE': 'critical'}):
            assert is_heavy_route_throttled('non_heavy_route') is False
    
    def test_get_throttling_response_format(self):
        """Test that throttling response has correct format"""
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            response = get_throttling_response()
            
            assert response['statusCode'] == 429
            assert response['headers']['Content-Type'] == 'application/json'
            assert response['headers']['Retry-After'] == '60'
            assert response['headers']['X-Safe-Mode'] == 'elevated'
            assert response['headers']['X-Rate-Limit-Reason'] == 'safe-mode-throttling'
            
            body = response['body']
            assert body['error'] == 'Service temporarily throttled'
            assert 'elevated' in body['message']
            assert body['safe_mode'] == 'elevated'
            assert body['retry_after'] == 60


class TestSafeModeRateLimitDecorator:
    """Test the safe mode aware rate limit decorator"""
    
    def test_normal_function_execution(self):
        """Test that decorator allows normal function execution"""
        @safe_mode_rate_limit_decorator('test_endpoint', tokens=1)
        def test_function():
            return "success"
        
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            result = test_function()
            assert result == "success"
    
    def test_heavy_route_throttling_in_decorator(self):
        """Test that heavy routes are throttled by decorator"""
        @safe_mode_rate_limit_decorator('timeline', tokens=1, heavy_route=True)
        def test_function():
            return "success"
        
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            result = test_function()
            
            # Should return throttling response instead of function result
            assert result['statusCode'] == 429
            assert 'elevated' in result['body']['message']
    
    def test_non_heavy_route_not_throttled_in_decorator(self):
        """Test that non-heavy routes are not throttled by decorator"""
        @safe_mode_rate_limit_decorator('test_endpoint', tokens=1, heavy_route=False)
        def test_function():
            return "success"
        
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            result = test_function()
            assert result == "success"
    
    @pytest.mark.asyncio
    async def test_async_function_support(self):
        """Test that decorator works with async functions"""
        @safe_mode_rate_limit_decorator('test_endpoint', tokens=1)
        async def test_async_function():
            return "async_success"
        
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            result = await test_async_function()
            assert result == "async_success"
    
    @pytest.mark.asyncio 
    async def test_async_heavy_route_throttling(self):
        """Test that async heavy routes are throttled"""
        @safe_mode_rate_limit_decorator('timeline', tokens=1, heavy_route=True)
        async def test_async_function():
            return "success"
        
        with patch.dict(os.environ, {'SAFE_MODE': 'critical'}):
            result = await test_async_function()
            
            # Should return throttling response
            assert result['statusCode'] == 429
            assert 'critical' in result['body']['message']
    
    def test_custom_key_function(self):
        """Test decorator with custom key extraction function"""
        call_count = 0
        
        def custom_key_func(*args, **kwargs):
            return "custom_key"
        
        @safe_mode_rate_limit_decorator('test_endpoint', tokens=1, key_func=custom_key_func)
        def test_function(user_id):
            nonlocal call_count
            call_count += 1
            return f"success_{call_count}"
        
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            result1 = test_function("user1")
            result2 = test_function("user2")
            
            assert result1 == "success_1"
            assert result2 == "success_2"


class TestSafeModeTransitions:
    """Test behavior during safe mode transitions"""
    
    def test_rate_limiter_adapts_to_mode_changes(self):
        """Test that rate limiter adapts when safe mode changes during runtime"""
        rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
        
        # Start in normal mode and get some tokens
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            bucket = rate_limiter._get_bucket('test_user')
            initial_tokens = bucket['tokens']
            assert initial_tokens == 100
        
        # Switch to emergency mode 
        with patch.dict(os.environ, {'SAFE_MODE': 'emergency'}):
            bucket = rate_limiter._get_bucket('test_user')
            # Should be limited to emergency levels
            assert bucket['tokens'] <= 10  # Emergency mode max tokens
    
    def test_throttling_behavior_during_transitions(self):
        """Test throttling behavior when safe mode transitions"""
        @safe_mode_rate_limit_decorator('timeline', tokens=1, heavy_route=True)
        def test_heavy_route():
            return "success"
        
        # Normal mode - should work
        with patch.dict(os.environ, {'SAFE_MODE': 'normal'}):
            result = test_heavy_route()
            assert result == "success"
        
        # Switch to elevated - should be throttled
        with patch.dict(os.environ, {'SAFE_MODE': 'elevated'}):
            result = test_heavy_route()
            assert result['statusCode'] == 429


if __name__ == '__main__':
    pytest.main([__file__])