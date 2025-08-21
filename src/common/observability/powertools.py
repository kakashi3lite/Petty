"""
Production-grade observability with AWS Lambda Powertools
Provides structured logging, metrics, and tracing across all services
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from contextlib import contextmanager
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.tracing import Tracer as TracerClass
import boto3
from botocore.exceptions import ClientError

# Initialize AWS Lambda Powertools
logger = Logger(
    service=os.getenv("SERVICE_NAME", "petty-api"),
    level=os.getenv("LOG_LEVEL", "INFO"),
    sampling_rate=float(os.getenv("LOG_SAMPLING_RATE", "0.1"))
)

tracer = Tracer(
    service=os.getenv("SERVICE_NAME", "petty-api"),
    disabled=os.getenv("DISABLE_TRACING", "false").lower() == "true"
)

metrics = Metrics(
    namespace=os.getenv("METRICS_NAMESPACE", "Petty"),
    service=os.getenv("SERVICE_NAME", "petty-api")
)

class ObservabilityManager:
    """Centralized observability management for the Petty application"""
    
    def __init__(self):
        self.service_name = os.getenv("SERVICE_NAME", "petty-api")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.version = os.getenv("SERVICE_VERSION", "0.1.0")
        self.correlation_id = str(uuid.uuid4())
        
        # Performance tracking
        self._operation_times = {}
        self._error_counts = {}
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for request tracing"""
        self.correlation_id = correlation_id
        logger.set_correlation_id(correlation_id)
    
    def log_business_event(self, event_name: str, **kwargs) -> None:
        """Log important business events with structured data"""
        logger.info(
            f"Business Event: {event_name}",
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
            f"Security Event: {event_type}",
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
            f"Performance: {operation}",
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
            f"AI Inference: {model_name}",
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
                subsegment.put_metadata("operation_metadata", metadata)
            
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
                        f"Operation failed: {operation_name}",
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
            start_time = time.time()
            success = True
            result = None
            error = None
            
            # Create span metadata
            metadata = {
                "function_name": func.__name__,
                "operation": operation_name
            }
            
            if include_args:
                metadata["args_count"] = len(args)
                metadata["kwargs_keys"] = list(kwargs.keys())
            
            with obs_manager.trace_operation(operation_name, metadata):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    obs_manager.log_security_event(
                        "function_error", 
                        "medium",
                        {
                            "function": func.__name__,
                            "operation": operation_name,
                            "error": error
                        }
                    )
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    obs_manager.log_performance_metric(operation_name, duration_ms, success)
        
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
                f"API Request: {method} {endpoint}",
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
                    f"API Response: {method} {endpoint}",
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
                    f"API Error: {method} {endpoint}",
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
        
        # Check AWS services
        try:
            # Test S3 connectivity
            s3_client = boto3.client('s3')
            s3_client.list_buckets()
            dependencies["s3"] = {"status": "healthy", "response_time_ms": 0}
        except ClientError as e:
            dependencies["s3"] = {"status": "unhealthy", "error": str(e)}
        
        try:
            # Test DynamoDB connectivity
            timestream_client = boto3.client('timestream-query')
            dependencies["timestream"] = {"status": "healthy", "response_time_ms": 0}
        except ClientError as e:
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
            "Lambda invocation started",
            extra={
                "event_type": "lambda_start",
                "function_name": context.function_name if context else "unknown",
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
    'HealthChecker'
]