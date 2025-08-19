"""
Rate limiting and circuit breaker - OWASP LLM04: Model Denial of Service
Integrated with safe mode for automated canary mitigation
"""

import time
import asyncio
import os
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass

class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass

class RateLimiter:
    """Token bucket rate limiter with safe mode integration"""
    
    def __init__(self, max_tokens: int, refill_rate: float, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_tokens: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
            window_seconds: Time window for rate limiting
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.window_seconds = window_seconds
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Store base values for safe mode calculations
        self._base_max_tokens = max_tokens
        self._base_refill_rate = refill_rate
    
    def _get_safe_mode_multiplier(self) -> float:
        """Get rate limit multiplier based on current safe mode"""
        safe_mode = os.getenv("SAFE_MODE", "normal").lower()
        
        multipliers = {
            "normal": 1.0,
            "elevated": 0.7,
            "critical": 0.3,
            "emergency": 0.1
        }
        
        return multipliers.get(safe_mode, 1.0)
    
    def _get_effective_limits(self) -> tuple[int, float]:
        """Get effective rate limits considering safe mode"""
        multiplier = self._get_safe_mode_multiplier()
        effective_max_tokens = int(self._base_max_tokens * multiplier)
        effective_refill_rate = self._base_refill_rate * multiplier
        return effective_max_tokens, effective_refill_rate
    
    def _get_bucket(self, key: str) -> Dict[str, Any]:
        """Get or create bucket for key"""
        now = time.time()
        effective_max_tokens, effective_refill_rate = self._get_effective_limits()
        
        if key not in self.buckets:
            self.buckets[key] = {
                'tokens': effective_max_tokens,
                'last_refill': now
            }
        
        bucket = self.buckets[key]
        
        # Refill tokens based on time elapsed
        time_elapsed = now - bucket['last_refill']
        tokens_to_add = time_elapsed * effective_refill_rate
        bucket['tokens'] = min(effective_max_tokens, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
        
        return bucket
    
    def acquire(self, key: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from bucket
        
        Args:
            key: Identifier for rate limit bucket (e.g., user_id, ip_address)
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False if rate limited
        """
        bucket = self._get_bucket(key)
        
        if bucket['tokens'] >= tokens:
            bucket['tokens'] -= tokens
            self.logger.debug(f"Rate limit acquired: {key}, tokens remaining: {bucket['tokens']}")
            return True
        else:
            self.logger.warning(f"Rate limit exceeded: {key}, tokens needed: {tokens}, available: {bucket['tokens']}")
            return False
    
    def check_limit(self, key: str, tokens: int = 1) -> None:
        """
        Check rate limit and raise exception if exceeded
        
        Args:
            key: Identifier for rate limit bucket
            tokens: Number of tokens to check
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        if not self.acquire(key, tokens):
            raise RateLimitExceeded(f"Rate limit exceeded for {key}")
    
    def get_remaining_tokens(self, key: str) -> int:
        """Get remaining tokens for key"""
        bucket = self._get_bucket(key)
        return int(bucket['tokens'])
    
    def reset_bucket(self, key: str) -> None:
        """Reset bucket for key"""
        if key in self.buckets:
            del self.buckets[key]
            self.logger.info(f"Rate limit bucket reset: {key}")

class CircuitBreaker:
    """Circuit breaker for service protection"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting to close circuit
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.logger = logging.getLogger(__name__)
    
    def _reset(self) -> None:
        """Reset circuit breaker to closed state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.logger.info("Circuit breaker reset to CLOSED")
    
    def _record_success(self) -> None:
        """Record successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self._reset()
        elif self.failure_count > 0:
            self.failure_count = 0
            self.logger.debug("Circuit breaker failure count reset")
    
    def _record_failure(self) -> None:
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _can_attempt(self) -> bool:
        """Check if operation can be attempted"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               (datetime.utcnow() - self.last_failure_time).seconds >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker moved to HALF_OPEN")
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpen: If circuit breaker is open
        """
        if not self._can_attempt():
            raise CircuitBreakerOpen("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise e
    
    async def acall(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of call"""
        if not self._can_attempt():
            raise CircuitBreakerOpen("Circuit breaker is open")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise e

# Global rate limiters for different endpoints
_rate_limiters = {
    'ingest': RateLimiter(max_tokens=100, refill_rate=10),  # 10 requests/sec, burst of 100
    'timeline': RateLimiter(max_tokens=20, refill_rate=2),   # 2 requests/sec, burst of 20
    'feedback': RateLimiter(max_tokens=50, refill_rate=5),   # 5 requests/sec, burst of 50
    'ai_inference': RateLimiter(max_tokens=10, refill_rate=0.5),  # 1 request/2sec, burst of 10
}

# Heavy routes that should be throttled in safe mode
HEAVY_ROUTES = {
    'timeline',   # Timeline generation with ML analysis
    'ingest',     # High-volume data processing  
    'feedback'    # Complex feedback processing
}


def is_heavy_route_throttled(endpoint: str) -> bool:
    """Check if a heavy route should be throttled based on safe mode"""
    safe_mode = os.getenv("SAFE_MODE", "normal").lower()
    
    # Only throttle heavy routes in non-normal safe modes
    if safe_mode == "normal":
        return False
        
    return endpoint in HEAVY_ROUTES


def get_throttling_response() -> Dict[str, Any]:
    """Get standardized 429 throttling response for safe mode"""
    safe_mode = os.getenv("SAFE_MODE", "normal").lower()
    
    return {
        "statusCode": 429,
        "headers": {
            "Content-Type": "application/json",
            "Retry-After": "60",
            "X-Safe-Mode": safe_mode,
            "X-Rate-Limit-Reason": "safe-mode-throttling"
        },
        "body": {
            "error": "Service temporarily throttled",
            "message": f"System is in {safe_mode} safe mode. Please try again later.",
            "safe_mode": safe_mode,
            "retry_after": 60
        }
    }


def safe_mode_rate_limit_decorator(
    endpoint: str,
    tokens: int = 1,
    key_func: Optional[Callable] = None,
    heavy_route: bool = False
):
    """
    Safe mode aware rate limiting decorator
    
    Args:
        endpoint: Rate limiter endpoint name
        tokens: Number of tokens to consume
        key_func: Function to extract rate limit key from arguments
        heavy_route: Whether this is a heavy route that should be throttled
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if heavy route should be throttled
            if heavy_route and is_heavy_route_throttled(endpoint):
                return get_throttling_response()
            
            # Extract rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default to using first argument as key or 'default'
                key = str(args[0]) if args else 'default'
            
            # Check rate limit
            rate_limiter = _rate_limiters.get(endpoint)
            if rate_limiter:
                try:
                    rate_limiter.check_limit(key, tokens)
                except RateLimitExceeded:
                    return get_throttling_response()
            
            return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check if heavy route should be throttled
            if heavy_route and is_heavy_route_throttled(endpoint):
                return get_throttling_response()
                
            # Extract rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default to using first argument as key or 'default'
                key = str(args[0]) if args else 'default'
            
            # Check rate limit
            rate_limiter = _rate_limiters.get(endpoint)
            if rate_limiter:
                try:
                    rate_limiter.check_limit(key, tokens)
                except RateLimitExceeded:
                    return get_throttling_response()
            
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

def rate_limit_decorator(
    endpoint: str,
    tokens: int = 1,
    key_func: Optional[Callable] = None
):
    """
    Decorator for rate limiting endpoints
    
    Args:
        endpoint: Rate limiter endpoint name
        tokens: Number of tokens to consume
        key_func: Function to extract rate limit key from arguments
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default to using first argument as key or 'default'
                key = str(args[0]) if args else 'default'
            
            # Check rate limit
            rate_limiter = _rate_limiters.get(endpoint)
            if rate_limiter:
                rate_limiter.check_limit(key, tokens)
            
            return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default to using first argument as key or 'default'
                key = str(args[0]) if args else 'default'
            
            # Check rate limit
            rate_limiter = _rate_limiters.get(endpoint)
            if rate_limiter:
                rate_limiter.check_limit(key, tokens)
            
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

def get_rate_limiter(endpoint: str) -> Optional[RateLimiter]:
    """Get rate limiter for endpoint"""
    return _rate_limiters.get(endpoint)

def add_rate_limiter(endpoint: str, rate_limiter: RateLimiter) -> None:
    """Add custom rate limiter for endpoint"""
    _rate_limiters[endpoint] = rate_limiter
