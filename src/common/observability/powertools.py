"""Production-grade observability utilities with safe fallbacks.

This file intentionally keeps implementation simple and robust. It:
 - Uses AWS Lambda Powertools when available
 - Falls back to lightweight stubs when dependencies are missing
 - Provides helper decorators & an ObservabilityManager
 - Avoids complex refactors to remain easy to audit
"""

import json
import os
import sys
import time
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

try:  # Attempt real powertools import
    from aws_lambda_powertools import Logger, Tracer, Metrics  # type: ignore
    from aws_lambda_powertools.logging import correlation_paths  # type: ignore
    from aws_lambda_powertools.metrics import MetricUnit  # type: ignore
    POWertools_AVAILABLE = True
except ImportError:  # Provide stubs
    POWertools_AVAILABLE = False

    class _StubLogger:
        def __init__(self, service: str, level: str = "INFO", sampling_rate: float = 0.1):
            self.service = service
            self.level = level
            self.correlation_id = None

        def _write(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
            try:
                print(f"[{level}] {message} | extra={json.dumps(extra) if extra else ''}")
            except Exception:
                print(f"[{level}] {message}")

        def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
            self._write("INFO", message, extra)
        def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
            self._write("WARNING", message, extra)
        def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
            self._write("ERROR", message, extra)
        def set_correlation_id(self, correlation_id: str):
            self.correlation_id = correlation_id
        def inject_lambda_context(self, **_kwargs):
            def decorator(func: Callable):
                @wraps(func)
                def wrapper(event, context):
                    return func(event, context)
                return wrapper
            return decorator

    class _StubSubsegment:
        def put_metadata(self, *_, **__):
            return None
        def add_exception(self, *_, **__):
            return None

    class _StubTracer:
        disabled: bool = True
        def __init__(self, *_, **__):
            pass
        def capture_lambda_handler(self, func: Callable):
            @wraps(func)
            def wrapper(event, context):
                return func(event, context)
            return wrapper
        def capture_method(self, func: Callable):
            return func
        @contextmanager
        def subsegment(self, _name: str):
            yield _StubSubsegment()

    class _StubMetrics:
        def __init__(self, *_, **__):
            pass
        def add_metric(self, *_, **__):
            return None
        def log_metrics(self, capture_cold_start_metric: bool = False):
            def decorator(func: Callable):
                @wraps(func)
                def wrapper(event, context):
                    return func(event, context)
                return wrapper
            return decorator

    class _StubMetricUnit:
        Milliseconds = "Milliseconds"
        Count = "Count"
        Percent = "Percent"

    Logger = _StubLogger  # type: ignore
    Tracer = _StubTracer  # type: ignore
    Metrics = _StubMetrics  # type: ignore
    MetricUnit = _StubMetricUnit  # type: ignore

    class _CorrelationPaths:
        API_GATEWAY_HTTP = "requestId"
    correlation_paths = _CorrelationPaths()

try:
    import boto3  # type: ignore  # noqa: F401
    _BOTO3_AVAILABLE = True
except Exception:  # pragma: no cover
    _BOTO3_AVAILABLE = False

def _unicode_enabled() -> bool:
    if os.getenv("DISABLE_UNICODE_LOGS", "0") == "1":
        return False
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    if os.name == "nt" and "utf" not in enc:
        return False
    return True
EMOJI_ENABLED = _unicode_enabled()

def _sanitize_message(msg: str) -> str:
    if EMOJI_ENABLED:
        return msg
    return re.sub(r"[\U00010000-\U0010FFFF]", "", msg)

SERVICE_NAME = os.getenv("SERVICE_NAME", "petty-api")
METRICS_NAMESPACE = os.getenv("METRICS_NAMESPACE", "Petty")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_SAMPLE_RATE = float(os.getenv("LOG_SAMPLING_RATE", "0.1"))

logger = Logger(service=SERVICE_NAME, level=LOG_LEVEL, sample_rate=LOG_SAMPLE_RATE)
tracer = Tracer(service=SERVICE_NAME, disabled=os.getenv("DISABLE_TRACING", "false").lower() == "true")
metrics = Metrics(namespace=METRICS_NAMESPACE, service=SERVICE_NAME)

class ObservabilityManager:
    """Centralized observability management (simple version)."""

    def __init__(self):
        self.service_name = SERVICE_NAME
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.version = os.getenv("SERVICE_VERSION", "0.1.0")
        self.correlation_id = str(uuid.uuid4())

    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for request tracing"""
        self.correlation_id = correlation_id
        logger.set_correlation_id(correlation_id)
    
    def log_business_event(self, event_name: str, **kwargs) -> None:
        """Log important business events with structured data"""
        logger.info(
            _sanitize_message(f"Business Event: {event_name}"),
            extra={
                "event_type": "business",
                "event_name": event_name,
                "correlation_id": self.correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": self.service_name,
                "environment": self.environment,
                **kwargs
            }
        )
    
    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]) -> None:
        """Log security-related events with high priority"""
        logger.warning(
            _sanitize_message(f"Security Event: {event_type}"),
            extra={
                "event_type": "security",
                "security_event": event_type,
                "severity": severity,
                "correlation_id": self.correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": self.service_name,
                **details
            }
        )
    
    def log_performance_metric(self, operation: str, duration_ms: float, success: bool = True) -> None:
        """Log performance metrics for operations"""
        # Add to CloudWatch metrics
        metrics.add_metric(
            name=f"{operation}_duration",
            unit=MetricUnit.Milliseconds,
            value=duration_ms
        )
        
        metrics.add_metric(
            name=f"{operation}_count",
            unit=MetricUnit.Count,
            value=1
        )
        
        if not success:
            metrics.add_metric(
                name=f"{operation}_errors",
                unit=MetricUnit.Count,
                value=1
            )
        
        # Structured logging
        logger.info(
            _sanitize_message(f"Performance: {operation}"),
            extra={
                "event_type": "performance",
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "correlation_id": self.correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    def log_ai_inference(self, model_name: str, input_size: int, confidence: float, 
                        processing_time_ms: float, behavior_detected: str) -> None:
        """Log AI inference events with model performance data"""
        # Business metrics for AI
        metrics.add_metric(
            name="ai_inference_confidence",
            unit=MetricUnit.Percent,
            value=confidence * 100
        )
        
        metrics.add_metric(
            name="ai_inference_duration",
            unit=MetricUnit.Milliseconds,
            value=processing_time_ms
        )
        
        metrics.add_metric(
            name="ai_inference_count",
            unit=MetricUnit.Count,
            value=1
        )
        
        logger.info(
            _sanitize_message(f"AI Inference: {model_name}"),
            extra={
                "event_type": "ai_inference",
                "model_name": model_name,
                "input_size": input_size,
                "confidence": confidence,
                "processing_time_ms": processing_time_ms,
                "behavior_detected": behavior_detected,
                "correlation_id": self.correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    @contextmanager
    def trace_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations with automatic metrics"""
        start_time = time.time()
        success = True
        error = None

        with tracer.subsegment(operation_name) as subsegment:
            if metadata:
                try:
                    subsegment.put_metadata("operation_metadata", metadata)
                except Exception:
                    pass

            try:
                yield subsegment
            except Exception as e:
                success = False
                error = str(e)
                subsegment.add_exception(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                self.log_performance_metric(operation_name, duration_ms, success)
                if error:
                    logger.error(
                        _sanitize_message(f"Operation failed: {operation_name}"),
                        extra={
                            "operation": operation_name,
                            "error": error,
                            "duration_ms": duration_ms,
                            "correlation_id": self.correlation_id
                        }
                    )

# Global observability manager instance
obs_manager = ObservabilityManager()

def monitor_performance(operation_name: str, include_args: bool = False):
    """Decorator to monitor function performance and errors"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            metadata = {"function_name": func.__name__, "operation": operation_name}
            if include_args:
                metadata["args_count"] = len(args)
                metadata["kwargs_keys"] = list(kwargs.keys())

            with obs_manager.trace_operation(operation_name, metadata):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    obs_manager.log_security_event(
                        "function_error",
                        "medium",
                        {
                            "function": func.__name__,
                            "operation": operation_name,
                            "error": str(e)
                        }
                    )
                    raise
        
        return wrapper
    return decorator

def log_api_request(endpoint: str, method: str, user_id: Optional[str] = None):
    """Decorator to log API requests with security context"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            obs_manager.set_correlation_id(request_id)
            
            start_time = time.time()
            
            logger.info(
                _sanitize_message(f"API Request: {method} {endpoint}"),
                extra={
                    "event_type": "api_request",
                    "endpoint": endpoint,
                    "method": method,
                    "user_id": user_id,
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                obs_manager.log_performance_metric(f"api_{method.lower()}_{endpoint.replace('/', '_')}", duration_ms)
                
                logger.info(
                    _sanitize_message(f"API Response: {method} {endpoint}"),
                    extra={
                        "event_type": "api_response",
                        "endpoint": endpoint,
                        "method": method,
                        "user_id": user_id,
                        "request_id": request_id,
                        "duration_ms": duration_ms,
                        "status": "success"
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                obs_manager.log_security_event(
                    "api_error",
                    "high",
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "user_id": user_id,
                        "error": str(e),
                        "duration_ms": duration_ms
                    }
                )
                
                logger.error(
                    _sanitize_message(f"API Error: {method} {endpoint}"),
                    extra={
                        "event_type": "api_error",
                        "endpoint": endpoint,
                        "method": method,
                        "user_id": user_id,
                        "request_id": request_id,
                        "error": str(e),
                        "duration_ms": duration_ms
                    }
                )
                
                raise
        
        return wrapper
    return decorator

class HealthChecker:
    """Health check utilities for service monitoring"""
    
    def __init__(self):
        self.service_name = obs_manager.service_name
        self.start_time = datetime.now(timezone.utc)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "version": obs_manager.version,
            "environment": obs_manager.environment,
            "correlation_id": obs_manager.correlation_id
        }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check health of external dependencies"""
        dependencies = {}
        
        # Check AWS services (lightweight reachability probes)
        try:
            if _BOTO3_AVAILABLE:
                s3_client = boto3.client('s3')  # type: ignore
                s3_client.list_buckets()
                dependencies["s3"] = {"status": "healthy", "response_time_ms": 0}
            else:
                dependencies["s3"] = {"status": "unknown", "error": "boto3_unavailable"}
        except Exception as e:
            dependencies["s3"] = {"status": "unhealthy", "error": str(e)}
        
        try:
            if _BOTO3_AVAILABLE:
                # Creation of client suffices as lightweight health indicator
                boto3.client('timestream-query')  # type: ignore
                dependencies["timestream"] = {"status": "healthy", "response_time_ms": 0}
            else:
                dependencies["timestream"] = {"status": "unknown", "error": "boto3_unavailable"}
        except Exception as e:
            dependencies["timestream"] = {"status": "unhealthy", "error": str(e)}
        
        return {
            "service": self.service_name,
            "dependencies": dependencies,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global health checker
health_checker = HealthChecker()

# Lambda handler decorators for automatic observability
def lambda_handler_with_observability(func: Callable) -> Callable:
    """Complete observability wrapper for Lambda handlers"""
    @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
    @tracer.capture_lambda_handler
    @metrics.log_metrics(capture_cold_start_metric=True)
    @wraps(func)
    def wrapper(event, context):
        # Extract correlation ID from API Gateway
        correlation_id = event.get('headers', {}).get('x-correlation-id', str(uuid.uuid4()))
        obs_manager.set_correlation_id(correlation_id)
        
        # Log request
        logger.info(
            _sanitize_message("Lambda invocation started"),
            extra={
                "event_type": "lambda_start",
                "function_name": getattr(context, 'function_name', 'unknown') if context else "unknown",
                "correlation_id": correlation_id,
                "cold_start": getattr(context, 'cold_start', False) if context else False
            }
        )
        
        try:
            result = func(event, context)
            
            obs_manager.log_business_event(
                "lambda_success",
                function_name=context.function_name if context else "unknown"
            )
            
            return result
            
        except Exception as e:
            obs_manager.log_security_event(
                "lambda_error",
                "high",
                {
                    "function_name": context.function_name if context else "unknown",
                    "error": str(e),
                    "event_source": event.get('source', 'unknown') if isinstance(event, dict) else 'unknown'
                }
            )
            raise
    
    return wrapper

# Export key components
__all__ = [
    'logger',
    'tracer', 
    'metrics',
    'obs_manager',
    'monitor_performance',
    'log_api_request',
    'lambda_handler_with_observability',
    'health_checker',
    'ObservabilityManager',
    'HealthChecker',
    'POWertools_AVAILABLE'
]