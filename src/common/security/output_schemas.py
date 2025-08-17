"""
Output validation and schema enforcement - OWASP LLM02: Insecure Output Handling
"""

from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field, field_validator

logger = structlog.get_logger(__name__)

class TimelineEventOutput(BaseModel):
    """Secure output schema for timeline events"""
    event_id: str = Field(..., pattern=r'^evt_[a-f0-9]{8}$')
    timestamp: datetime = Field(...)
    behavior: str = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: str | None = Field(None, max_length=500)
    metadata: dict[str, Any] | None = Field(default_factory=dict)

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        """Sanitize description output"""
        if v is None:
            return None

        # Remove any potential script tags or suspicious content
        sanitized = v.replace('<', '&lt;').replace('>', '&gt;')
        sanitized = sanitized.replace('javascript:', '').replace('data:', '')
        return sanitized[:500]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TimelineOutput(BaseModel):
    """Secure output schema for complete timeline"""
    pet_id: str = Field(..., pattern=r'^pet_[a-f0-9]{8,16}$')
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    events: list[TimelineEventOutput] = Field(...)
    summary: str | None = Field(None, max_length=1000)
    risk_flags: list[str] = Field(default_factory=list)

    @field_validator('events')
    @classmethod
    def validate_events_count(cls, v: list[TimelineEventOutput]) -> list[TimelineEventOutput]:
        """Limit number of events to prevent DoS"""
        if len(v) > 100:
            raise ValueError("Too many events in timeline (max 100)")
        return v

    @field_validator('summary')
    @classmethod
    def sanitize_summary(cls, v: str | None) -> str | None:
        """Sanitize summary text"""
        if v is None:
            return None

        # Remove potential script content
        sanitized = v.replace('<', '&lt;').replace('>', '&gt;')
        sanitized = sanitized.replace('javascript:', '').replace('data:', '')
        return sanitized[:1000]

    @field_validator('risk_flags')
    @classmethod
    def validate_risk_flags(cls, v: list[str]) -> list[str]:
        """Validate risk flags"""
        allowed_flags = {
            'high_stress', 'low_activity', 'irregular_heartrate',
            'potential_injury', 'environmental_concern', 'behavioral_change'
        }

        validated_flags = []
        for flag in v[:10]:  # Max 10 flags
            if flag in allowed_flags:
                validated_flags.append(flag)

        return validated_flags

class BehaviorAnalysisOutput(BaseModel):
    """Secure output schema for behavior analysis"""
    analysis_id: str = Field(..., pattern=r'^analysis_[a-f0-9]{8}$')
    behaviors_detected: list[TimelineEventOutput] = Field(...)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)

    @field_validator('behaviors_detected')
    @classmethod
    def validate_behavior_count(cls, v: list[TimelineEventOutput]) -> list[TimelineEventOutput]:
        """Limit number of behaviors"""
        if len(v) > 50:
            raise ValueError("Too many behaviors detected (max 50)")
        return v

    @field_validator('recommendations')
    @classmethod
    def sanitize_recommendations(cls, v: list[str]) -> list[str]:
        """Sanitize recommendation text"""
        sanitized = []
        for rec in v[:20]:  # Max 20 recommendations
            clean_rec = rec.replace('<', '&lt;').replace('>', '&gt;')
            clean_rec = clean_rec.replace('javascript:', '').replace('data:', '')
            sanitized.append(clean_rec[:200])
        return sanitized

    @field_validator('alerts')
    @classmethod
    def sanitize_alerts(cls, v: list[str]) -> list[str]:
        """Sanitize alert text"""
        sanitized = []
        for alert in v[:10]:  # Max 10 alerts
            clean_alert = alert.replace('<', '&lt;').replace('>', '&gt;')
            clean_alert = clean_alert.replace('javascript:', '').replace('data:', '')
            sanitized.append(clean_alert[:200])
        return sanitized

class APIResponse(BaseModel):
    """Standardized API response wrapper"""
    success: bool = Field(...)
    data: dict[str, Any] | list[Any] | None = Field(None)
    message: str | None = Field(None, max_length=500)
    error_code: str | None = Field(None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str | None = Field(None, pattern=r'^req_[a-f0-9]{8,16}$')

    @field_validator('message')
    @classmethod
    def sanitize_message(cls, v: str | None) -> str | None:
        """Sanitize response message"""
        if v is None:
            return None

        # Remove potential script content
        sanitized = v.replace('<', '&lt;').replace('>', '&gt;')
        sanitized = sanitized.replace('javascript:', '').replace('data:', '')
        return sanitized[:500]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OutputValidator:
    """Central output validation service"""

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def validate_timeline_output(self, data: dict[str, Any]) -> TimelineOutput:
        """Validate timeline output"""
        try:
            validated = TimelineOutput(**data)
            self.logger.info(
                "Timeline output validated",
                pet_id=validated.pet_id,
                events_count=len(validated.events),
                risk_flags=validated.risk_flags
            )
            return validated
        except Exception as e:
            self.logger.error(
                "Timeline output validation failed",
                error=str(e),
                data_keys=list(data.keys()) if isinstance(data, dict) else "not_dict"
            )
            raise ValueError(f"Invalid timeline output: {e}")

    def validate_behavior_output(self, data: dict[str, Any]) -> BehaviorAnalysisOutput:
        """Validate behavior analysis output"""
        try:
            validated = BehaviorAnalysisOutput(**data)
            self.logger.info(
                "Behavior output validated",
                analysis_id=validated.analysis_id,
                behaviors_count=len(validated.behaviors_detected),
                confidence=validated.confidence_score
            )
            return validated
        except Exception as e:
            self.logger.error(
                "Behavior output validation failed",
                error=str(e),
                data_keys=list(data.keys()) if isinstance(data, dict) else "not_dict"
            )
            raise ValueError(f"Invalid behavior output: {e}")

    def create_secure_response(
        self,
        success: bool,
        data: dict[str, Any] | list[Any] | None = None,
        message: str | None = None,
        error_code: str | None = None,
        request_id: str | None = None
    ) -> dict[str, Any]:
        """Create a secure API response"""
        try:
            response = APIResponse(
                success=success,
                data=data,
                message=message,
                error_code=error_code,
                request_id=request_id
            )

            response_dict = response.dict()

            self.logger.info(
                "Secure response created",
                success=success,
                has_data=data is not None,
                request_id=request_id
            )

            return response_dict

        except Exception as e:
            self.logger.error(
                "Failed to create secure response",
                error=str(e),
                success=success
            )
            # Fallback to minimal safe response
            return {
                "success": False,
                "message": "Internal error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }

def validate_timeline_output(data: dict[str, Any]) -> TimelineOutput:
    """Convenience function for timeline output validation"""
    validator = OutputValidator()
    return validator.validate_timeline_output(data)

def validate_behavior_output(data: dict[str, Any]) -> BehaviorAnalysisOutput:
    """Convenience function for behavior output validation"""
    validator = OutputValidator()
    return validator.validate_behavior_output(data)

def secure_response_wrapper(
    success: bool,
    data: dict[str, Any] | list[Any] | None = None,
    message: str | None = None,
    error_code: str | None = None,
    request_id: str | None = None
) -> dict[str, Any]:
    """Convenience function for creating secure responses"""
    validator = OutputValidator()
    return validator.create_secure_response(success, data, message, error_code, request_id)
