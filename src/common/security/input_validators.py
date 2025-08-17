"""
Input validation module - OWASP LLM01: Prompt Injection & LLM02: Insecure Output Handling
"""

import re
import html
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, ValidationError
import structlog

logger = structlog.get_logger(__name__)

# Allowed patterns for various inputs
ALLOWED_COLLAR_ID_PATTERN = re.compile(r'^[A-Z]{2}-\d{3,6}$')
ALLOWED_BEHAVIOR_TYPES = {
    'Deep Sleep', 'Anxious Pacing', 'Playing Fetch', 'Eating', 'Drinking',
    'Walking', 'Running', 'Resting', 'Alert', 'Unknown'
}
MAX_TEXT_LENGTH = 1000
MAX_COORDS_PRECISION = 6  # Decimal places for GPS coordinates

class CollarDataModel(BaseModel):
    """Secure model for collar sensor data"""
    collar_id: str = Field(..., pattern=r'^[A-Z]{2}-\d{3,6}$')
    timestamp: datetime = Field(...)
    heart_rate: int = Field(..., ge=30, le=300)  # BPM range for dogs
    activity_level: int = Field(..., ge=0, le=2)
    location: Dict[str, Any] = Field(...)
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is UTC and within reasonable bounds"""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        # Reject timestamps more than 1 hour in the future or 30 days in the past
        now = datetime.now(timezone.utc)
        if v > now.replace(hour=now.hour + 1):
            raise ValueError("Timestamp cannot be more than 1 hour in the future")
        if (now - v).days > 30:
            raise ValueError("Timestamp cannot be more than 30 days old")
        
        return v
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate GPS coordinates and structure"""
        if not isinstance(v, dict):
            raise ValueError("Location must be a dictionary")
        
        if v.get('type') != 'Point':
            raise ValueError("Location type must be 'Point'")
        
        coords = v.get('coordinates', [])
        if not isinstance(coords, list) or len(coords) != 2:
            raise ValueError("Coordinates must be a list of [longitude, latitude]")
        
        lon, lat = coords
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError("Coordinates must be numeric")
        
        # Validate coordinate bounds
        if not (-180 <= lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        
        # Limit precision to prevent fingerprinting
        coords[0] = round(float(lon), MAX_COORDS_PRECISION)
        coords[1] = round(float(lat), MAX_COORDS_PRECISION)
        
        return v

class UserFeedbackModel(BaseModel):
    """Secure model for user feedback"""
    event_id: str = Field(..., pattern=r'^evt_[a-f0-9]{8}$')
    feedback: str = Field(..., pattern=r'^(positive|negative)$')
    user_id: Optional[str] = Field(None, pattern=r'^usr_[a-f0-9]{8,16}$')
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class BehaviorEventModel(BaseModel):
    """Secure model for behavior events"""
    event_id: str = Field(..., pattern=r'^evt_[a-f0-9]{8}$')
    behavior: str = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(...)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('behavior')
    @classmethod
    def validate_behavior(cls, v: str) -> str:
        """Ensure behavior is from allowed set"""
        if v not in ALLOWED_BEHAVIOR_TYPES:
            raise ValueError(f"Behavior must be one of: {ALLOWED_BEHAVIOR_TYPES}")
        return v
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata to prevent injection"""
        if v is None:
            return {}
        
        # Limit metadata size and sanitize strings
        sanitized = {}
        for key, value in v.items():
            if len(sanitized) >= 10:  # Max 10 metadata fields
                break
            
            # Sanitize key
            clean_key = sanitize_text_input(str(key)[:50])
            if not clean_key:
                continue
                
            # Sanitize value
            if isinstance(value, str):
                clean_value = sanitize_text_input(value[:200])
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            else:
                clean_value = sanitize_text_input(str(value)[:200])
            
            sanitized[clean_key] = clean_value
        
        return sanitized

class InputValidator:
    """Central input validation service"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def validate_collar_data(self, data: Dict[str, Any]) -> CollarDataModel:
        """Validate collar sensor data"""
        try:
            validated = CollarDataModel(**data)
            self.logger.info(
                "Collar data validated",
                collar_id=validated.collar_id,
                timestamp=validated.timestamp.isoformat()
            )
            return validated
        except ValidationError as e:
            self.logger.warning(
                "Invalid collar data",
                errors=str(e),
                data_keys=list(data.keys())
            )
            raise ValueError(f"Invalid collar data: {e}")
    
    def validate_user_feedback(self, data: Dict[str, Any]) -> UserFeedbackModel:
        """Validate user feedback data"""
        try:
            validated = UserFeedbackModel(**data)
            self.logger.info(
                "User feedback validated",
                event_id=validated.event_id,
                feedback=validated.feedback
            )
            return validated
        except ValidationError as e:
            self.logger.warning(
                "Invalid user feedback",
                errors=str(e),
                data_keys=list(data.keys())
            )
            raise ValueError(f"Invalid user feedback: {e}")
    
    def validate_behavior_event(self, data: Dict[str, Any]) -> BehaviorEventModel:
        """Validate behavior event data"""
        try:
            validated = BehaviorEventModel(**data)
            self.logger.info(
                "Behavior event validated",
                event_id=validated.event_id,
                behavior=validated.behavior,
                confidence=validated.confidence
            )
            return validated
        except ValidationError as e:
            self.logger.warning(
                "Invalid behavior event",
                errors=str(e),
                data_keys=list(data.keys())
            )
            raise ValueError(f"Invalid behavior event: {e}")

def sanitize_text_input(text: str) -> str:
    """Sanitize text input to prevent injection attacks"""
    if not isinstance(text, str):
        text = str(text)
    
    # Limit length
    text = text[:MAX_TEXT_LENGTH]
    
    # HTML escape
    text = html.escape(text)
    
    # Remove control characters except newline and tab
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Remove potential SQL injection patterns
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND)\b)',
        r'(--|/\*|\*/)',
        r'(\b(EXEC|EXECUTE|SP_)\b)',
    ]
    
    for pattern in sql_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove potential command injection patterns
    cmd_patterns = [
        r'[;&|`$()]',
        r'\b(rm|del|format|shutdown|reboot)\b',
    ]
    
    for pattern in cmd_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def validate_collar_data(data: Dict[str, Any]) -> CollarDataModel:
    """Convenience function for collar data validation"""
    validator = InputValidator()
    return validator.validate_collar_data(data)

def validate_user_feedback(data: Dict[str, Any]) -> UserFeedbackModel:
    """Convenience function for user feedback validation"""
    validator = InputValidator()
    return validator.validate_user_feedback(data)
