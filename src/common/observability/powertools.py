"""
AWS Lambda Powertools integration for unified observability
"""

import os
import logging
from typing import Optional

try:
    from aws_lambda_powertools import Logger, Tracer, Metrics
    from aws_lambda_powertools.logging import correlation_paths
    from aws_lambda_powertools.metrics import MetricUnit
    AWS_POWERTOOLS_AVAILABLE = True
except ImportError:
    AWS_POWERTOOLS_AVAILABLE = False

# Global instances for singleton pattern
_logger: Optional[Logger] = None
_tracer: Optional[Tracer] = None
_metrics: Optional[Metrics] = None


def setup_powertools(service_name: Optional[str] = None) -> tuple:
    """
    Setup AWS Lambda Powertools logger, tracer, and metrics.
    
    Args:
        service_name: Override service name from environment
        
    Returns:
        Tuple of (logger, tracer, metrics)
    """
    global _logger, _tracer, _metrics
    
    if not AWS_POWERTOOLS_AVAILABLE:
        # Fallback for environments without powertools
        fallback_logger = logging.getLogger(service_name or "petty")
        fallback_logger.setLevel(logging.INFO)
        return fallback_logger, None, None
    
    # Get service name from environment or parameter
    service = service_name or os.getenv("POWERTOOLS_SERVICE_NAME", "petty")
    log_level = os.getenv("POWERTOOLS_LOG_LEVEL", "INFO")
    
    if _logger is None:
        _logger = Logger(
            service=service,
            level=log_level,
            sample_rate=0.1,  # Sample 10% for cost optimization
            log_uncaught_exceptions=True
        )
    
    if _tracer is None:
        _tracer = Tracer(service=service)
    
    if _metrics is None:
        _metrics = Metrics(
            service=service,
            namespace="Petty"
        )
    
    return _logger, _tracer, _metrics


def get_logger() -> Logger:
    """Get the global logger instance"""
    if _logger is None:
        setup_powertools()
    return _logger


def get_tracer() -> Tracer:
    """Get the global tracer instance"""
    if _tracer is None:
        setup_powertools()
    return _tracer


def get_metrics() -> Metrics:
    """Get the global metrics instance"""
    if _metrics is None:
        setup_powertools()
    return _metrics


def add_request_metric():
    """Add a request count metric"""
    if _metrics and AWS_POWERTOOLS_AVAILABLE:
        _metrics.add_metric(name="Requests", unit=MetricUnit.Count, value=1)