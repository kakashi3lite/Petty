"""
Production-grade tracing module with AWS X-Ray integration
Handles distributed tracing for performance and error analysis
"""

import os
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, cast

# Fallback for when X-Ray is not available
HAS_XRAY = False
try:
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    HAS_XRAY = True
except ImportError:
    logging.warning("AWS X-Ray SDK not installed - using stub implementation")

# Type definitions
F = TypeVar('F', bound=Callable[..., Any])

def setup_tracing(service_name: str) -> None:
    """
    Set up X-Ray tracing for the service.
    
    Args:
        service_name: Name of the service for X-Ray segments
    """
    if HAS_XRAY:
        try:
            xray_recorder.configure(
                service=service_name,
                context_missing='LOG_ERROR'
            )
            patch_all()
            logging.info(f"X-Ray tracing configured for {service_name}")
        except Exception as e:
            logging.error(f"Failed to configure X-Ray: {e}")
    else:
        logging.info(f"Using stub tracing for {service_name} (X-Ray not available)")

def trace_function(name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator for tracing functions with X-Ray.
    
    Args:
        name: Custom name for the trace segment
        
    Returns:
        Decorated function with tracing
    """
    def decorator(func: F) -> F:
        func_name = name or func.__name__
        
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if HAS_XRAY:
                segment_name = f"{func_name}"
                with xray_recorder.capture(segment_name) as segment:
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        if segment:
                            segment.add_exception(e)
                        raise
            else:
                # Just call the function if X-Ray is not available
                return func(*args, **kwargs)
                
        return cast(F, wrapper)
    return decorator

def get_tracer(service_name: str) -> Any:
    """
    Get a configured tracer instance.
    
    Args:
        service_name: Name of the service
        
    Returns:
        Tracer instance or stub if X-Ray is not available
    """
    if HAS_XRAY:
        setup_tracing(service_name)
        return xray_recorder
    else:
        # Return a stub tracer with no-op methods
        class StubTracer:
            def begin_segment(self, name: str) -> None:
                pass
                
            def end_segment(self) -> None:
                pass
                
            def begin_subsegment(self, name: str) -> None:
                pass
                
            def end_subsegment(self) -> None:
                pass
                
            def put_annotation(self, key: str, value: Any) -> None:
                pass
                
            def put_metadata(self, key: str, value: Any, namespace: str = 'default') -> None:
                pass
                
            def capture(self, name: str) -> Any:
                class StubContext:
                    def __enter__(self):
                        return None
                    def __exit__(self, exc_type, exc_val, exc_tb):
                        pass
                return StubContext()
        
        return StubTracer()
