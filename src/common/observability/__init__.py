"""
Observability module with AWS Lambda Powertools integration
"""

from .logger import setup_structured_logging, get_logger, log_with_context

try:
    from .powertools import get_powertools_logger, get_powertools_tracer, get_powertools_metrics
    __all__ = [
        "setup_structured_logging",
        "get_logger", 
        "log_with_context",
        "get_powertools_logger",
        "get_powertools_tracer",
        "get_powertools_metrics",
    ]
except ImportError:
    __all__ = [
        "setup_structured_logging",
        "get_logger", 
        "log_with_context",
    ]
