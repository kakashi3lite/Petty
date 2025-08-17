"""
Structured logging with AWS Lambda Powertools
"""

import json
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any

try:
    from aws_lambda_powertools import Logger
    from aws_lambda_powertools.logging import correlation_paths
    AWS_POWERTOOLS_AVAILABLE = True
except ImportError:
    AWS_POWERTOOLS_AVAILABLE = False

# Fallback logger configuration
class StructuredLogger:
    """Structured logger with security-aware formatting"""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs) -> None:
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._log("ERROR", message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        self._log("DEBUG", message, **kwargs)

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with structured format"""
        # Sanitize kwargs to prevent log injection
        sanitized_kwargs = self._sanitize_log_data(kwargs)

        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": self._sanitize_message(message),
            "service": os.getenv("SERVICE_NAME", "petty"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            **sanitized_kwargs
        }

        getattr(self.logger, level.lower())(json.dumps(log_data))

    def _sanitize_message(self, message: str) -> str:
        """Sanitize log message to prevent injection"""
        if not isinstance(message, str):
            message = str(message)

        # Remove newlines and control characters
        message = message.replace('\n', ' ').replace('\r', ' ')
        message = ''.join(char for char in message if ord(char) >= 32 or char == ' ')

        return message[:1000]  # Limit message length

    def _sanitize_log_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize log data to prevent injection and remove PII"""
        sanitized = {}

        # Fields that should be redacted
        sensitive_fields = {
            'password', 'token', 'key', 'secret', 'credential',
            'auth', 'session', 'cookie', 'ssn', 'credit_card'
        }

        for key, value in data.items():
            # Limit number of fields
            if len(sanitized) >= 20:
                break

            # Sanitize key
            clean_key = str(key)[:50].replace('.', '_').replace(' ', '_')

            # Check if field should be redacted
            if any(sensitive in clean_key.lower() for sensitive in sensitive_fields):
                sanitized[clean_key] = "[REDACTED]"
                continue

            # Sanitize value
            if isinstance(value, str):
                clean_value = self._sanitize_message(value)
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            elif isinstance(value, dict):
                # Recursively sanitize nested dict (limit depth)
                clean_value = self._sanitize_log_data(value) if len(str(value)) < 1000 else "[COMPLEX_OBJECT]"
            elif isinstance(value, list):
                # Sanitize list elements (limit length)
                clean_value = [self._sanitize_message(str(item)) for item in value[:10]]
            else:
                clean_value = self._sanitize_message(str(value))

            sanitized[clean_key] = clean_value

        return sanitized

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""

    def format(self, record):
        # If message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, TypeError):
            # Format as structured log
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            return json.dumps(log_data)

# Global logger instance
_logger: StructuredLogger | None = None

def setup_structured_logging(
    service_name: str = "petty",
    level: str = "INFO",
    use_powertools: bool = True
) -> StructuredLogger:
    """Setup structured logging"""
    global _logger

    if AWS_POWERTOOLS_AVAILABLE and use_powertools:
        # Use AWS Lambda Powertools logger
        powertools_logger = Logger(
            service=service_name,
            level=level,
            sample_rate=0.1,  # Sample 10% of logs for cost optimization
            log_uncaught_exceptions=True
        )

        # Wrap powertools logger with our interface
        class PowertoolsWrapper(StructuredLogger):
            def __init__(self, powertools_logger):
                self.powertools_logger = powertools_logger

            def info(self, message: str, **kwargs) -> None:
                self.powertools_logger.info(message, extra=kwargs)

            def warning(self, message: str, **kwargs) -> None:
                self.powertools_logger.warning(message, extra=kwargs)

            def error(self, message: str, **kwargs) -> None:
                self.powertools_logger.error(message, extra=kwargs)

            def debug(self, message: str, **kwargs) -> None:
                self.powertools_logger.debug(message, extra=kwargs)

        _logger = PowertoolsWrapper(powertools_logger)
    else:
        # Use fallback logger
        _logger = StructuredLogger(service_name, level)

    return _logger

def get_logger() -> StructuredLogger:
    """Get global logger instance"""
    global _logger
    if _logger is None:
        _logger = setup_structured_logging()
    return _logger

def log_with_context(func):
    """Decorator to add context to function logs"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        function_name = func.__name__

        logger.debug(
            f"Function {function_name} started",
            function=function_name,
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )

        try:
            result = func(*args, **kwargs)
            logger.debug(
                f"Function {function_name} completed",
                function=function_name,
                success=True
            )
            return result
        except Exception as e:
            logger.error(
                f"Function {function_name} failed",
                function=function_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    return wrapper
