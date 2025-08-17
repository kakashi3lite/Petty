"""
Rate limiting and circuit breaker - OWASP LLM04: Model Denial of Service
"""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

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
    """Token bucket rate limiter"""

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
        self.buckets: dict[str, dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    def _get_bucket(self, key: str) -> dict[str, Any]:
        """Get or create bucket for key"""
        now = time.time()

        if key not in self.buckets:
            self.buckets[key] = {
                'tokens': self.max_tokens,
                'last_refill': now
            }

        bucket = self.buckets[key]

        # Refill tokens based on time elapsed
        time_elapsed = now - bucket['last_refill']
        tokens_to_add = time_elapsed * self.refill_rate
        bucket['tokens'] = min(self.max_tokens, bucket['tokens'] + tokens_to_add)
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
        self.last_failure_time: datetime | None = None
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

def rate_limit_decorator(
    endpoint: str,
    tokens: int = 1,
    key_func: Callable | None = None
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

def get_rate_limiter(endpoint: str) -> RateLimiter | None:
    """Get rate limiter for endpoint"""
    return _rate_limiters.get(endpoint)

def add_rate_limiter(endpoint: str, rate_limiter: RateLimiter) -> None:
    """Add custom rate limiter for endpoint"""
    _rate_limiters[endpoint] = rate_limiter
