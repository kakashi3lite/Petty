"""
Pydantic v2 models for API boundary validation.

This module provides strict input validation models for API endpoints,
enforcing fail-closed behavior on unknown fields and strong type checking.
"""

from datetime import datetime, timezone
from typing import Literal, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LocationPoint(BaseModel):
    """GeoJSON Point for location data."""
    
    model_config = ConfigDict(
        extra='forbid',  # Fail-closed on unknown fields
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=True  # Immutable for security
    )
    
    type: Literal["Point"] = Field(
        description="GeoJSON type, must be 'Point'"
    )
    coordinates: List[float] = Field(
        min_length=2,
        max_length=2,
        description="Longitude and latitude coordinates [lon, lat]"
    )
    
    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        """Validate coordinate bounds and precision."""
        if len(v) != 2:
            raise ValueError("Coordinates must contain exactly [longitude, latitude]")
        
        lon, lat = v
        
        # Validate coordinate bounds
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude {lon} must be between -180 and 180")
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude {lat} must be between -90 and 90")
        
        # Limit precision to prevent fingerprinting attacks
        return [round(lon, 6), round(lat, 6)]


class TelemetryIn(BaseModel):
    """Input model for telemetry data ingestion."""
    
    model_config = ConfigDict(
        extra='forbid',  # Fail-closed on unknown fields
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    collar_id: str = Field(
        pattern=r'^[A-Z]{2}-\d{3,6}$',
        description="Collar identifier in format XX-123456"
    )
    timestamp: datetime = Field(
        description="ISO timestamp when data was collected"
    )
    heart_rate: int = Field(
        ge=30,
        le=300,
        description="Heart rate in BPM, valid range for dogs"
    )
    activity_level: int = Field(
        ge=0,
        le=2,
        description="Activity level: 0=rest, 1=moderate, 2=high"
    )
    location: LocationPoint = Field(
        description="GPS location as GeoJSON Point"
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is recent and in proper format."""
        # Convert to UTC if timezone-naive
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        # Basic sanity check - not too far in future
        now = datetime.now(timezone.utc)
        if v > now.replace(hour=23, minute=59, second=59):
            raise ValueError("Timestamp cannot be in the future")
        
        return v


class CollarIdQuery(BaseModel):
    """Input model for collar ID query parameters."""
    
    model_config = ConfigDict(
        extra='forbid',  # Fail-closed on unknown fields
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=True  # Immutable for security
    )
    
    collar_id: str = Field(
        pattern=r'^[A-Z]{2}-\d{3,6}$',
        description="Collar identifier in format XX-123456"
    )


class FeedbackIn(BaseModel):
    """Input model for user feedback."""
    
    model_config = ConfigDict(
        extra='forbid',  # Fail-closed on unknown fields
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=True  # Immutable for security
    )
    
    event_id: str = Field(
        pattern=r'^evt_[a-f0-9]{8}$',
        description="Event identifier in format evt_12345678"
    )
    user_feedback: Literal["correct", "incorrect"] = Field(
        description="User feedback on the event classification"
    )
    user_id: Optional[str] = Field(
        default=None,
        pattern=r'^usr_[a-f0-9]{8,16}$',
        description="Optional user identifier"
    )


def validate_telemetry_input(data: dict) -> TelemetryIn:
    """
    Validate telemetry input data and return first validation error.
    
    Args:
        data: Raw input data dictionary
        
    Returns:
        Validated TelemetryIn model
        
    Raises:
        ValueError: With first validation error message
    """
    try:
        return TelemetryIn.model_validate(data)
    except Exception as e:
        # Extract first error message
        if hasattr(e, 'errors') and e.errors():
            first_error = e.errors()[0]
            field = '.'.join(str(loc) for loc in first_error['loc'])
            message = first_error['msg']
            raise ValueError(f"Validation error in field '{field}': {message}")
        raise ValueError(f"Validation error: {str(e)}")


def validate_collar_query(data: dict) -> CollarIdQuery:
    """
    Validate collar ID query parameters.
    
    Args:
        data: Raw query parameters dictionary
        
    Returns:
        Validated CollarIdQuery model
        
    Raises:
        ValueError: With first validation error message
    """
    try:
        return CollarIdQuery.model_validate(data)
    except Exception as e:
        if hasattr(e, 'errors') and e.errors():
            first_error = e.errors()[0]
            field = '.'.join(str(loc) for loc in first_error['loc'])
            message = first_error['msg']
            raise ValueError(f"Validation error in field '{field}': {message}")
        raise ValueError(f"Validation error: {str(e)}")


def validate_feedback_input(data: dict) -> FeedbackIn:
    """
    Validate feedback input data.
    
    Args:
        data: Raw input data dictionary
        
    Returns:
        Validated FeedbackIn model
        
    Raises:
        ValueError: With first validation error message
    """
    try:
        return FeedbackIn.model_validate(data)
    except Exception as e:
        if hasattr(e, 'errors') and e.errors():
            first_error = e.errors()[0]
            field = '.'.join(str(loc) for loc in first_error['loc'])
            message = first_error['msg']
            raise ValueError(f"Validation error in field '{field}': {message}")
        raise ValueError(f"Validation error: {str(e)}")