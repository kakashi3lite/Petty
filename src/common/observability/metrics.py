"""
Production-grade metrics collection module with AWS CloudWatch integration
Handles application metrics and KPIs for monitoring and alerting
"""

import os
import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast
from functools import wraps

# Fallback for when CloudWatch Metrics is not available
HAS_METRICS = False
try:
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit
    HAS_METRICS = True
except ImportError:
    logging.warning("AWS Lambda Powertools Metrics not installed - using stub implementation")
    
    # Stub metric units for local development
    class MetricUnit:
        Count = "Count"
        Seconds = "Seconds"
        Milliseconds = "Milliseconds"
        Microseconds = "Microseconds"
        Bytes = "Bytes"
        Kilobytes = "Kilobytes"
        Megabytes = "Megabytes"
        Gigabytes = "Gigabytes"
        Terabytes = "Terabytes"
        Percent = "Percent"
        None_ = "None"

# Type definitions
F = TypeVar('F', bound=Callable[..., Any])

# Global metrics client
_metrics_client = None

def setup_metrics(namespace: str, service: Optional[str] = None) -> Any:
    """
    Set up CloudWatch metrics for the service.
    
    Args:
        namespace: CloudWatch metrics namespace
        service: Service name (defaults to namespace if not provided)
        
    Returns:
        Metrics client
    """
    global _metrics_client
    
    if HAS_METRICS:
        try:
            service_name = service or namespace
            _metrics_client = Metrics(namespace=namespace, service=service_name)
            logging.info(f"CloudWatch metrics configured for {service_name}")
            return _metrics_client
        except Exception as e:
            logging.error(f"Failed to configure CloudWatch metrics: {e}")
            
    # Return stub metrics client if CloudWatch is not available
    _metrics_client = StubMetrics(namespace, service or namespace)
    return _metrics_client

def get_metrics() -> Any:
    """
    Get the metrics client.
    
    Returns:
        Metrics client
    """
    global _metrics_client
    if _metrics_client is None:
        service_name = os.getenv("SERVICE_NAME", "petty-service")
        return setup_metrics(service_name)
    return _metrics_client

def record_metric(name: str, value: float = 1, unit: str = MetricUnit.Count, dimensions: Optional[Dict[str, str]] = None) -> None:
    """
    Record a metric to CloudWatch.
    
    Args:
        name: Metric name
        value: Metric value
        unit: Metric unit
        dimensions: Additional dimensions for the metric
    """
    metrics = get_metrics()
    
    if HAS_METRICS:
        try:
            metrics.add_metric(name=name, value=value, unit=unit)
            if dimensions:
                for key, val in dimensions.items():
                    metrics.add_dimension(name=key, value=val)
            metrics.flush_metrics()
        except Exception as e:
            logging.error(f"Failed to record metric {name}: {e}")
    else:
        # Log the metric locally if CloudWatch is not available
        dim_str = f", dimensions={dimensions}" if dimensions else ""
        logging.info(f"METRIC: {name}={value} {unit}{dim_str}")

class StubMetrics:
    """Stub implementation of CloudWatch Metrics for local development"""
    
    def __init__(self, namespace: str, service: str):
        self.namespace = namespace
        self.service = service
        self.metrics = []
        self.dimensions = {}
        
    def add_metric(self, name: str, value: float, unit: str = MetricUnit.Count) -> None:
        """Add a metric to the buffer"""
        self.metrics.append({
            "name": name,
            "value": value,
            "unit": unit,
            "timestamp": time.time()
        })
        
    def add_dimension(self, name: str, value: str) -> None:
        """Add a dimension to all metrics"""
        self.dimensions[name] = value
        
    def flush_metrics(self) -> None:
        """Log metrics and clear the buffer"""
        for metric in self.metrics:
            dims = ", ".join([f"{k}={v}" for k, v in self.dimensions.items()])
            dims_str = f", dimensions=[{dims}]" if dims else ""
            logging.info(
                f"STUB METRIC: {metric['name']}={metric['value']} "
                f"{metric['unit']}{dims_str}"
            )
        self.metrics = []
        self.dimensions = {}
