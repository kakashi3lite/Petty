"""
AWS Lambda Powertools integration for structured logging, tracing, and metrics.
"""

import os
from typing import Optional
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit


def get_powertools_logger(service_name: Optional[str] = None) -> Logger:
    """Get a configured powertools logger."""
    service = service_name or os.getenv("POWERTOOLS_SERVICE_NAME", "petty")
    log_level = os.getenv("POWERTOOLS_LOG_LEVEL", "INFO")
    
    return Logger(
        service=service,
        level=log_level,
        log_uncaught_exceptions=True
    )


def get_powertools_tracer(service_name: Optional[str] = None) -> Tracer:
    """Get a configured powertools tracer."""
    service = service_name or os.getenv("POWERTOOLS_SERVICE_NAME", "petty")
    
    return Tracer(service=service)


def get_powertools_metrics(service_name: Optional[str] = None, namespace: str = "Petty") -> Metrics:
    """Get a configured powertools metrics instance."""
    service = service_name or os.getenv("POWERTOOLS_SERVICE_NAME", "petty")
    
    return Metrics(
        service=service,
        namespace=namespace
    )