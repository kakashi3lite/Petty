"""
Tests for Pydantic v2 models in models.py
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from src.common.security.models import (
    TelemetryIn,
    LocationPoint,
    CollarIdQuery,
    FeedbackIn,
    validate_telemetry_input,
    validate_collar_query,
    validate_feedback_input,
)


class TestLocationPoint:
    """Test cases for LocationPoint model."""
    
    def test_valid_location_point(self):
        """Test valid location point creation."""
        data = {
            "type": "Point",
            "coordinates": [-74.0060, 40.7128]  # NYC
        }
        location = LocationPoint.model_validate(data)
        assert location.type == "Point"
        assert location.coordinates == [-74.0060, 40.7128]
    
    def test_coordinate_precision_limiting(self):
        """Test that coordinates are limited to 6 decimal places."""
        data = {
            "type": "Point", 
            "coordinates": [-74.00600123456789, 40.71280987654321]
        }
        location = LocationPoint.model_validate(data)
        assert location.coordinates == [-74.006001, 40.712810]
    
    def test_invalid_longitude_bounds(self):
        """Test longitude bounds validation."""
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "Point",
                "coordinates": [-181.0, 40.7128]
            })
        assert "Longitude -181.0 must be between -180 and 180" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "Point", 
                "coordinates": [181.0, 40.7128]
            })
        assert "Longitude 181.0 must be between -180 and 180" in str(exc_info.value)
    
    def test_invalid_latitude_bounds(self):
        """Test latitude bounds validation."""
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "Point",
                "coordinates": [-74.0060, -91.0]
            })
        assert "Latitude -91.0 must be between -90 and 90" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "Point",
                "coordinates": [-74.0060, 91.0]
            })
        assert "Latitude 91.0 must be between -90 and 90" in str(exc_info.value)
    
    def test_invalid_coordinate_count(self):
        """Test that exactly 2 coordinates are required."""
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "Point",
                "coordinates": [-74.0060]  # Only one coordinate
            })
        # Pydantic's built-in list length validation triggers first
        assert "List should have at least 2 items" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "Point",
                "coordinates": [-74.0060, 40.7128, 100.0]  # Three coordinates
            })
        # Pydantic's built-in list length validation triggers first
        assert "List should have at most 2 items" in str(exc_info.value)
    
    def test_invalid_type(self):
        """Test that type must be 'Point'."""
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "LineString",
                "coordinates": [-74.0060, 40.7128]
            })
        assert "Input should be 'Point'" in str(exc_info.value)
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            LocationPoint.model_validate({
                "type": "Point",
                "coordinates": [-74.0060, 40.7128],
                "extra_field": "not allowed"
            })
        assert "Extra inputs are not permitted" in str(exc_info.value)


class TestTelemetryIn:
    """Test cases for TelemetryIn model."""
    
    def test_valid_telemetry_data(self):
        """Test valid telemetry data creation."""
        data = {
            "collar_id": "AB-123456",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.0060, 40.7128]
            }
        }
        telemetry = TelemetryIn.model_validate(data)
        assert telemetry.collar_id == "AB-123456"
        assert telemetry.heart_rate == 85
        assert telemetry.activity_level == 1
        assert telemetry.location.type == "Point"
    
    def test_invalid_collar_id_format(self):
        """Test collar ID format validation."""
        data = {
            "collar_id": "invalid",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]}
        }
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate(data)
        assert "String should match pattern" in str(exc_info.value)
    
    def test_heart_rate_bounds(self):
        """Test heart rate bounds validation."""
        base_data = {
            "collar_id": "AB-123456",
            "timestamp": "2024-01-15T10:30:00Z",
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]}
        }
        
        # Too low
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate({**base_data, "heart_rate": 29})
        assert "Input should be greater than or equal to 30" in str(exc_info.value)
        
        # Too high
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate({**base_data, "heart_rate": 301})
        assert "Input should be less than or equal to 300" in str(exc_info.value)
    
    def test_activity_level_bounds(self):
        """Test activity level bounds validation."""
        base_data = {
            "collar_id": "AB-123456",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]}
        }
        
        # Too low
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate({**base_data, "activity_level": -1})
        assert "Input should be greater than or equal to 0" in str(exc_info.value)
        
        # Too high
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate({**base_data, "activity_level": 3})
        assert "Input should be less than or equal to 2" in str(exc_info.value)
    
    def test_future_timestamp_validation(self):
        """Test that future timestamps are rejected."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        data = {
            "collar_id": "AB-123456",
            "timestamp": future_time.isoformat(),
            "heart_rate": 85,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]}
        }
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate(data)
        assert "Timestamp cannot be in the future" in str(exc_info.value)
    
    def test_missing_required_fields(self):
        """Test that all required fields must be present."""
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate({})
        errors = str(exc_info.value)
        assert "Field required" in errors
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        data = {
            "collar_id": "AB-123456",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]},
            "extra_field": "not allowed"
        }
        with pytest.raises(ValidationError) as exc_info:
            TelemetryIn.model_validate(data)
        assert "Extra inputs are not permitted" in str(exc_info.value)


class TestCollarIdQuery:
    """Test cases for CollarIdQuery model."""
    
    def test_valid_collar_query(self):
        """Test valid collar ID query."""
        data = {"collar_id": "AB-123456"}
        query = CollarIdQuery.model_validate(data)
        assert query.collar_id == "AB-123456"
    
    def test_invalid_collar_id_format(self):
        """Test collar ID format validation."""
        with pytest.raises(ValidationError) as exc_info:
            CollarIdQuery.model_validate({"collar_id": "invalid"})
        assert "String should match pattern" in str(exc_info.value)
    
    def test_missing_collar_id(self):
        """Test that collar_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            CollarIdQuery.model_validate({})
        assert "Field required" in str(exc_info.value)
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            CollarIdQuery.model_validate({
                "collar_id": "AB-123456",
                "extra_field": "not allowed"
            })
        assert "Extra inputs are not permitted" in str(exc_info.value)


class TestFeedbackIn:
    """Test cases for FeedbackIn model."""
    
    def test_valid_feedback(self):
        """Test valid feedback creation."""
        data = {
            "event_id": "evt_12345678", 
            "user_feedback": "correct"
        }
        feedback = FeedbackIn.model_validate(data)
        assert feedback.event_id == "evt_12345678"
        assert feedback.user_feedback == "correct"
        assert feedback.user_id is None
    
    def test_valid_feedback_with_user_id(self):
        """Test valid feedback with user ID."""
        data = {
            "event_id": "evt_12345678",
            "user_feedback": "incorrect", 
            "user_id": "usr_abcdef12"
        }
        feedback = FeedbackIn.model_validate(data)
        assert feedback.user_id == "usr_abcdef12"
    
    def test_invalid_event_id_format(self):
        """Test event ID format validation."""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackIn.model_validate({
                "event_id": "invalid",
                "user_feedback": "correct"
            })
        assert "String should match pattern" in str(exc_info.value)
    
    def test_invalid_user_feedback_value(self):
        """Test user feedback value validation."""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackIn.model_validate({
                "event_id": "evt_12345678",
                "user_feedback": "invalid"
            })
        assert "Input should be 'correct' or 'incorrect'" in str(exc_info.value)
    
    def test_invalid_user_id_format(self):
        """Test user ID format validation."""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackIn.model_validate({
                "event_id": "evt_12345678",
                "user_feedback": "correct",
                "user_id": "invalid"
            })
        assert "String should match pattern" in str(exc_info.value)
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackIn.model_validate({
                "event_id": "evt_12345678",
                "user_feedback": "correct",
                "extra_field": "not allowed"
            })
        assert "Extra inputs are not permitted" in str(exc_info.value)


class TestValidationHelpers:
    """Test cases for validation helper functions."""
    
    def test_validate_telemetry_input_success(self):
        """Test successful telemetry validation."""
        data = {
            "collar_id": "AB-123456",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]}
        }
        result = validate_telemetry_input(data)
        assert isinstance(result, TelemetryIn)
        assert result.collar_id == "AB-123456"
    
    def test_validate_telemetry_input_error(self):
        """Test telemetry validation error handling."""
        data = {"collar_id": "invalid"}
        with pytest.raises(ValueError) as exc_info:
            validate_telemetry_input(data)
        assert "Validation error in field" in str(exc_info.value)
    
    def test_validate_collar_query_success(self):
        """Test successful collar query validation."""
        data = {"collar_id": "AB-123456"}
        result = validate_collar_query(data)
        assert isinstance(result, CollarIdQuery)
        assert result.collar_id == "AB-123456"
    
    def test_validate_collar_query_error(self):
        """Test collar query validation error handling."""
        data = {"collar_id": "invalid"}
        with pytest.raises(ValueError) as exc_info:
            validate_collar_query(data)
        assert "Validation error in field" in str(exc_info.value)
    
    def test_validate_feedback_input_success(self):
        """Test successful feedback validation."""
        data = {"event_id": "evt_12345678", "user_feedback": "correct"}
        result = validate_feedback_input(data)
        assert isinstance(result, FeedbackIn)
        assert result.event_id == "evt_12345678"
    
    def test_validate_feedback_input_error(self):
        """Test feedback validation error handling."""
        data = {"event_id": "invalid"}
        with pytest.raises(ValueError) as exc_info:
            validate_feedback_input(data)
        assert "Validation error in field" in str(exc_info.value)