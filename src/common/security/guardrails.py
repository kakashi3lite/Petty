"""
AI Security Guardrails - OWASP LLM Top 10 Mitigations

This module provides comprehensive security guardrails for AI inference endpoints,
implementing protections against the OWASP LLM Top 10 threats.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timezone
from functools import wraps
import structlog

from pydantic import BaseModel, Field, ValidationError, field_validator
from .input_validators import InputValidator, sanitize_text_input
from .output_schemas import OutputValidator
from .rate_limiter import rate_limit_decorator

logger = structlog.get_logger(__name__)

# OWASP LLM01: Prompt Injection - Keyword Denylist
PROMPT_INJECTION_KEYWORDS = {
    # Common injection patterns
    'ignore previous instructions',
    'disregard above',
    'forget everything',
    'new instructions:',
    'override system',
    'admin mode',
    'developer mode',
    'debug mode',
    'maintenance mode',
    'jailbreak',
    'roleplay as',
    'pretend to be',
    'act as if',
    
    # SQL injection patterns
    'drop table',
    'delete from',
    'insert into',
    'update set',
    'union select',
    
    # System commands
    'rm -rf',
    'del /f',
    'format c:',
    'sudo',
    'exec(',
    'eval(',
    'system(',
    'shell_exec',
    
    # Script injection
    '<script',
    'javascript:',
    'data:text/html',
    'onload=',
    'onerror=',
    'onclick=',
}

# Size limits
MAX_INPUT_SIZE = 10000  # characters
MAX_OUTPUT_SIZE = 50000  # characters
MAX_PROFILE_FIELDS = 20
MAX_NESTED_DEPTH = 5


class AIInputModel(BaseModel):
    """Secure model for AI inference inputs"""
    profile: Dict[str, Any] = Field(...)
    request_id: Optional[str] = Field(None, pattern=r'^req_[a-f0-9]{8,16}$')
    client_info: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @field_validator('profile')
    @classmethod
    def validate_profile(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize pet profile data"""
        if not isinstance(v, dict):
            raise ValueError("Profile must be a dictionary")
        
        # Limit number of fields
        if len(v) > MAX_PROFILE_FIELDS:
            raise ValueError(f"Profile cannot have more than {MAX_PROFILE_FIELDS} fields")
        
        # Validate and sanitize each field
        sanitized = {}
        for key, value in v.items():
            # Sanitize key
            clean_key = sanitize_text_input(str(key)[:50])
            if not clean_key:
                continue
            
            # Sanitize value based on type
            if isinstance(value, str):
                # Check input size
                if len(value) > MAX_INPUT_SIZE:
                    raise ValueError(f"Text field '{key}' exceeds maximum length")
                # Check for prompt injection BEFORE sanitization
                if _contains_injection_keywords(value.lower()):
                    raise ValueError(f"Field '{key}' contains suspicious content")
                clean_value = sanitize_text_input(value)
            elif isinstance(value, (int, float)):
                clean_value = value
            elif isinstance(value, bool):
                clean_value = value
            elif isinstance(value, dict):
                # Limit nesting depth
                clean_value = _sanitize_nested_dict(value, depth=1)
            elif isinstance(value, list):
                # Limit list size and sanitize elements
                if len(value) > 100:
                    raise ValueError(f"List field '{key}' too large")
                clean_value = [sanitize_text_input(str(item)[:200]) for item in value[:100]]
            else:
                # Convert to string and sanitize
                clean_value = sanitize_text_input(str(value)[:200])
            
            sanitized[clean_key] = clean_value
        
        return sanitized


class AIPlanOutput(BaseModel):
    """Secure output schema for AI-generated plans"""
    pet_profile: Dict[str, Any] = Field(...)
    nutritional_plan: Dict[str, Any] = Field(...)
    health_alerts: List[str] = Field(default_factory=list)
    activity_plan: Dict[str, Any] = Field(...)
    request_id: Optional[str] = Field(None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('health_alerts')
    @classmethod
    def validate_health_alerts(cls, v: List[str]) -> List[str]:
        """Sanitize health alert messages"""
        if len(v) > 10:  # Limit number of alerts
            v = v[:10]
        
        sanitized_alerts = []
        for alert in v:
            if isinstance(alert, str):
                # Sanitize and check length
                clean_alert = sanitize_text_input(alert[:500])
                if clean_alert and not _contains_injection_keywords(clean_alert.lower()):
                    sanitized_alerts.append(clean_alert)
        
        return sanitized_alerts


def _contains_injection_keywords(text: str) -> bool:
    """Check if text contains prompt injection keywords"""
    text_lower = text.lower()
    for keyword in PROMPT_INJECTION_KEYWORDS:
        if keyword in text_lower:
            logger.warning(
                "Prompt injection keyword detected",
                keyword=keyword,
                text_preview=text[:100]
            )
            return True
    return False


def _sanitize_nested_dict(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
    """Recursively sanitize nested dictionary with depth limiting"""
    if depth > MAX_NESTED_DEPTH:
        return {}
    
    sanitized = {}
    for key, value in data.items():
        if len(sanitized) >= MAX_PROFILE_FIELDS:
            break
            
        clean_key = sanitize_text_input(str(key)[:50])
        if not clean_key:
            continue
            
        if isinstance(value, str):
            clean_value = sanitize_text_input(value[:500])
            if not _contains_injection_keywords(clean_value.lower()):
                sanitized[clean_key] = clean_value
        elif isinstance(value, (int, float, bool)):
            sanitized[clean_key] = value
        elif isinstance(value, dict):
            sanitized[clean_key] = _sanitize_nested_dict(value, depth + 1)
        elif isinstance(value, list):
            # Sanitize list elements
            clean_list = []
            for item in value[:10]:  # Limit list size
                if isinstance(item, str):
                    clean_item = sanitize_text_input(str(item)[:200])
                    if not _contains_injection_keywords(clean_item.lower()):
                        clean_list.append(clean_item)
                elif isinstance(item, (int, float, bool)):
                    clean_list.append(item)
            sanitized[clean_key] = clean_list
    
    return sanitized


class AIGuardrails:
    """Main guardrails service for AI inference endpoints"""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.output_validator = OutputValidator()
        self.logger = structlog.get_logger(__name__)
    
    def validate_input(self, profile: Dict[str, Any], **kwargs) -> AIInputModel:
        """
        Validate and sanitize AI inference input
        
        Args:
            profile: Pet profile data
            **kwargs: Additional input parameters
            
        Returns:
            Validated AIInputModel
            
        Raises:
            ValueError: If input validation fails
        """
        try:
            # Check total input size
            total_size = len(json.dumps(profile, default=str))
            if total_size > MAX_INPUT_SIZE:
                raise ValueError(f"Input size {total_size} exceeds maximum {MAX_INPUT_SIZE}")
            
            # Validate using Pydantic model
            validated_input = AIInputModel(
                profile=profile,
                request_id=kwargs.get('request_id'),
                client_info=kwargs.get('client_info', {})
            )
            
            self.logger.info(
                "AI input validated successfully",
                profile_fields=len(validated_input.profile),
                request_id=validated_input.request_id
            )
            
            return validated_input
            
        except ValidationError as e:
            self.logger.warning(
                "AI input validation failed",
                errors=str(e),
                profile_keys=list(profile.keys()) if isinstance(profile, dict) else "not_dict"
            )
            raise ValueError(f"Invalid AI input: {e}")
        except Exception as e:
            self.logger.error(
                "Unexpected error during input validation",
                error=str(e)
            )
            raise ValueError(f"Input validation error: {e}")
    
    def validate_output(self, plan: Dict[str, Any]) -> AIPlanOutput:
        """
        Validate and sanitize AI inference output
        
        Args:
            plan: AI-generated plan data
            
        Returns:
            Validated AIPlanOutput
            
        Raises:
            ValueError: If output validation fails
        """
        try:
            # Check output size
            total_size = len(json.dumps(plan, default=str))
            if total_size > MAX_OUTPUT_SIZE:
                raise ValueError(f"Output size {total_size} exceeds maximum {MAX_OUTPUT_SIZE}")
            
            # Validate using Pydantic model
            validated_output = AIPlanOutput(**plan)
            
            self.logger.info(
                "AI output validated successfully",
                health_alerts_count=len(validated_output.health_alerts),
                confidence_score=validated_output.confidence_score
            )
            
            return validated_output
            
        except ValidationError as e:
            self.logger.warning(
                "AI output validation failed",
                errors=str(e),
                plan_keys=list(plan.keys()) if isinstance(plan, dict) else "not_dict"
            )
            raise ValueError(f"Invalid AI output: {e}")
        except Exception as e:
            self.logger.error(
                "Unexpected error during output validation",
                error=str(e)
            )
            raise ValueError(f"Output validation error: {e}")
    
    def create_secure_response(
        self, 
        plan: AIPlanOutput, 
        success: bool = True,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a secure API response"""
        return self.output_validator.create_secure_response(
            success=success,
            data=plan.dict() if plan else None,
            message=message,
            request_id=plan.request_id if plan else None
        )


# Rate limiting decorator specifically for AI endpoints
def ai_rate_limit(
    max_requests_per_minute: int = 10,
    max_requests_per_hour: int = 100,
    key_func: Optional[Callable] = None
):
    """
    Rate limiting decorator for AI inference endpoints
    
    Args:
        max_requests_per_minute: Maximum requests per minute per key
        max_requests_per_hour: Maximum requests per hour per key
        key_func: Function to extract rate limit key from arguments
    """
    def decorator(func: Callable) -> Callable:
        # Apply both minute and hour rate limits
        func = rate_limit_decorator(
            endpoint=f"{func.__name__}_minute",
            tokens=max_requests_per_minute,
            key_func=key_func
        )(func)
        
        func = rate_limit_decorator(
            endpoint=f"{func.__name__}_hour", 
            tokens=max_requests_per_hour,
            key_func=key_func
        )(func)
        
        return func
    
    return decorator


def secure_ai_endpoint(
    rate_limit_per_minute: int = 10,
    rate_limit_per_hour: int = 100,
    key_func: Optional[Callable] = None
):
    """
    Complete security decorator for AI endpoints
    
    Combines input validation, output validation, and rate limiting
    """
    def decorator(func: Callable) -> Callable:
        
        @ai_rate_limit(
            max_requests_per_minute=rate_limit_per_minute,
            max_requests_per_hour=rate_limit_per_hour,
            key_func=key_func
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            guardrails = AIGuardrails()
            
            try:
                # Handle instance methods (args[0] is self, args[1] is profile)
                profile_arg = None
                if len(args) >= 2 and isinstance(args[1], dict):
                    # Instance method: args[0] = self, args[1] = profile
                    profile_arg = args[1]
                    call_args = args
                elif len(args) >= 1 and isinstance(args[0], dict):
                    # Function: args[0] = profile
                    profile_arg = args[0]
                    call_args = args
                else:
                    # No profile argument found, call original function
                    result = func(*args, **kwargs)
                    if isinstance(result, dict):
                        validated_output = guardrails.validate_output(result)
                        return guardrails.create_secure_response(validated_output)
                    return result
                
                # Validate input
                validated_input = guardrails.validate_input(profile_arg, **kwargs)
                
                # Reconstruct arguments with validated profile
                if len(args) >= 2:
                    # Instance method
                    new_args = (args[0], validated_input.profile) + args[2:]
                else:
                    # Function
                    new_args = (validated_input.profile,) + args[1:]
                
                # Call original function with validated input
                result = func(*new_args, **kwargs)
                
                # Validate output
                validated_output = guardrails.validate_output(result)
                
                # Return secure response
                return guardrails.create_secure_response(validated_output)
                    
            except ValueError as e:
                logger.warning(
                    "AI endpoint security validation failed",
                    function=func.__name__,
                    error=str(e)
                )
                return guardrails.output_validator.create_secure_response(
                    success=False,
                    message=f"Security validation failed: {e}",
                    error_code="VALIDATION_ERROR"
                )
            except Exception as e:
                logger.error(
                    "Unexpected error in secure AI endpoint",
                    function=func.__name__,
                    error=str(e)
                )
                return guardrails.output_validator.create_secure_response(
                    success=False,
                    message="Internal error occurred",
                    error_code="INTERNAL_ERROR"
                )
        
        return wrapper
    return decorator


# Convenience function for IP-based rate limiting
def extract_client_ip(*args, **kwargs) -> str:
    """Extract client IP from request headers or use default"""
    client_info = kwargs.get('client_info', {})
    return client_info.get('x-forwarded-for', client_info.get('remote_addr', 'unknown'))


# Global guardrails instance
guardrails = AIGuardrails()