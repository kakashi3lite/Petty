"""Centralized AWS Lambda Powertools utilities.

Exposes structured logger, tracer, and metrics objects configured via environment variables:
- POWERTOOLS_SERVICE_NAME: logical service name (defaults to 'petty-service')
- POWERTOOLS_LOG_LEVEL: log level (defaults to 'INFO')

Usage in Lambda handlers:

    from common.observability.powertools import logger, tracer, metrics

    @tracer.capture_lambda_handler
    @logger.inject_lambda_context(log_event=True)
    def lambda_handler(event, context):
        logger.append_keys(collar_id="SN-123")
        metrics.add_metric(name="Requests", unit=MetricUnit.Count, value=1)
        ...

Falls back gracefully if aws_lambda_powertools is unavailable (e.g., local minimal env), providing no-op shims.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

try:
    from aws_lambda_powertools import Logger, Metrics, Tracer
    from aws_lambda_powertools.metrics import MetricUnit
except ImportError:  # pragma: no cover - executed only when dependency missing
    Logger = Tracer = Metrics = None  # type: ignore
    class MetricUnit:  # minimal shim
        Count = "Count"
        Seconds = "Seconds"

POWERTOOLS_SERVICE_NAME = os.getenv("POWERTOOLS_SERVICE_NAME", "petty-service")
POWERTOOLS_LOG_LEVEL = os.getenv("POWERTOOLS_LOG_LEVEL", "INFO")

if Logger and Tracer and Metrics:
    logger = Logger(service=POWERTOOLS_SERVICE_NAME, level=POWERTOOLS_LOG_LEVEL)
    tracer = Tracer(service=POWERTOOLS_SERVICE_NAME)
    metrics = Metrics(service=POWERTOOLS_SERVICE_NAME, namespace="Petty")
else:  # Fallback lightweight shims
    class _Fallback:
        def __init__(self, name: str):
            self._name = name
        def __getattr__(self, item: str) -> Callable[..., Any]:
            def _noop(*_a: Any, **_kw: Any) -> Any:
                return None
            return _noop
        def append_keys(self, **_kw: Any) -> None:  # mimic powertools logger method
            return None
    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func
    logger = _Fallback("logger")  # type: ignore
    tracer = _Fallback("tracer")  # type: ignore
    metrics = _Fallback("metrics")  # type: ignore
    tracer.capture_lambda_handler = lambda func: func  # type: ignore
    logger.inject_lambda_context = lambda **_kw: (lambda f: f)  # type: ignore

__all__ = ["MetricUnit", "logger", "metrics", "tracer"]
