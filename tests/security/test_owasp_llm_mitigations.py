"""
Security tests for OWASP LLM Top 10 mitigations
"""

import pytest
import json
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st

# Import the modules we want to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from common.security.input_validators import (
        InputValidator, 
        validate_collar_data,
        sanitize_text_input,
        CollarDataModel
    )
    from common.security.output_schemas import (
        OutputValidator,
        validate_timeline_output,
        secure_response_wrapper
    )
    from common.security.rate_limiter import (
        RateLimiter,
        RateLimitExceeded,
        CircuitBreaker,
        CircuitBreakerOpen
    )
    from behavioral_interpreter.interpreter import BehavioralInterpreter
    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False

pytestmark = pytest.mark.security

class TestInputValidation:
    """Test LLM01: Prompt Injection mitigations"""
    
    def test_valid_collar_data(self):
        """Test that valid collar data passes validation"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        validator = InputValidator()
        valid_data = {
            "collar_id": "SN-123",
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006, 40.7128]
            }
        }
        
        result = validator.validate_collar_data(valid_data)
        assert result.collar_id == "SN-123"
        assert result.heart_rate == 85
    
    def test_invalid_collar_id_format(self):
        """Test that invalid collar ID format is rejected"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        validator = InputValidator()
        invalid_data = {
            "collar_id": "'; DROP TABLE collars; --",  # SQL injection attempt
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 85,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }
        
        with pytest.raises(ValueError, match="Invalid collar data"):
            validator.validate_collar_data(invalid_data)
    
    def test_heart_rate_bounds(self):
        """Test heart rate validation bounds"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        validator = InputValidator()
        
        # Test out of bounds heart rates
        invalid_cases = [
            {"heart_rate": 25},  # Too low
            {"heart_rate": 350}, # Too high
            {"heart_rate": -10}, # Negative
        ]
        
        for case in invalid_cases:
            invalid_data = {
                "collar_id": "SN-123",
                "timestamp": datetime.now(timezone.utc),
                "heart_rate": case["heart_rate"],
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            }
            
            with pytest.raises(ValueError):
                validator.validate_collar_data(invalid_data)
    
    def test_coordinate_precision_limiting(self):
        """Test that GPS coordinates are limited to prevent fingerprinting"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        validator = InputValidator()
        high_precision_data = {
            "collar_id": "SN-123",
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006000123456789, 40.712800987654321]  # High precision
            }
        }
        
        result = validator.validate_collar_data(high_precision_data)
        coords = result.location["coordinates"]
        
        # Check that precision is limited to 6 decimal places
        assert len(str(coords[0]).split('.')[1]) <= 6
        assert len(str(coords[1]).split('.')[1]) <= 6
    
    @given(st.text(min_size=1, max_size=2000))
    def test_text_sanitization_property(self, input_text):
        """Property-based test for text sanitization"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        sanitized = sanitize_text_input(input_text)
        
        # Properties that should always hold
        assert len(sanitized) <= 1000  # Length limit
        assert '<script' not in sanitized.lower()  # No script tags
        assert 'javascript:' not in sanitized.lower()  # No javascript protocols
        assert '--' not in sanitized  # No SQL comment syntax
        assert ';' not in sanitized  # No SQL statement terminators

class TestOutputValidation:
    """Test LLM02: Insecure Output Handling mitigations"""
    
    def test_timeline_output_validation(self):
        """Test timeline output validation and sanitization"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        validator = OutputValidator()
        
        timeline_data = {
            "pet_id": "pet_abc12345",
            "date": "2025-08-16",
            "events": [
                {
                    "event_id": "evt_12345678",
                    "timestamp": datetime.now(timezone.utc),
                    "behavior": "Deep Sleep",
                    "confidence": 0.92,
                    "description": "Pet appears to be in deep sleep state"
                }
            ],
            "summary": "Pet had a restful day with normal activity patterns",
            "risk_flags": ["low_activity"]
        }
        
        result = validator.validate_timeline_output(timeline_data)
        assert result.pet_id == "pet_abc12345"
        assert len(result.events) == 1
        assert result.events[0].behavior == "Deep Sleep"
    
    def test_malicious_output_sanitization(self):
        """Test that malicious content in outputs is sanitized"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        validator = OutputValidator()
        
        malicious_timeline = {
            "pet_id": "pet_abc12345",
            "date": "2025-08-16",
            "events": [
                {
                    "event_id": "evt_12345678",
                    "timestamp": datetime.now(timezone.utc),
                    "behavior": "Deep Sleep",
                    "confidence": 0.92,
                    "description": "<script>alert('xss')</script>Pet sleeping"  # XSS attempt
                }
            ],
            "summary": "javascript:alert('xss')Normal day",  # XSS attempt
            "risk_flags": []
        }
        
        result = validator.validate_timeline_output(malicious_timeline)
        
        # Check that malicious content is sanitized
        assert '<script>' not in result.events[0].description
        assert 'javascript:' not in result.summary
        assert '&lt;script&gt;' in result.events[0].description  # Should be HTML escaped
    
    def test_output_size_limits(self):
        """Test that output size is limited to prevent DoS"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        validator = OutputValidator()
        
        # Create a timeline with too many events
        excessive_events = []
        for i in range(150):  # More than the 100 limit
            excessive_events.append({
                "event_id": f"evt_{i:08d}",
                "timestamp": datetime.now(timezone.utc),
                "behavior": "Deep Sleep",
                "confidence": 0.9
            })
        
        timeline_data = {
            "pet_id": "pet_abc12345",
            "date": "2025-08-16",
            "events": excessive_events,
            "summary": "Too many events",
            "risk_flags": []
        }
        
        with pytest.raises(ValueError, match="Too many events"):
            validator.validate_timeline_output(timeline_data)

class TestRateLimiting:
    """Test LLM04: Model Denial of Service mitigations"""
    
    def test_rate_limiter_allows_within_limits(self):
        """Test that rate limiter allows requests within limits"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        rate_limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
        
        # Should allow initial requests
        for i in range(5):
            assert rate_limiter.acquire(f"user_{i}", 1) == True
    
    def test_rate_limiter_blocks_excessive_requests(self):
        """Test that rate limiter blocks requests exceeding limits"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        rate_limiter = RateLimiter(max_tokens=5, refill_rate=0.1)  # Low refill rate
        
        # Exhaust the bucket
        for i in range(5):
            assert rate_limiter.acquire("user1", 1) == True
        
        # Next request should be blocked
        assert rate_limiter.acquire("user1", 1) == False
    
    def test_rate_limiter_per_user_isolation(self):
        """Test that rate limiting is isolated per user"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        rate_limiter = RateLimiter(max_tokens=5, refill_rate=0.1)
        
        # Exhaust bucket for user1
        for i in range(5):
            assert rate_limiter.acquire("user1", 1) == True
        
        # user2 should still have full bucket
        assert rate_limiter.acquire("user2", 1) == True
        
        # user1 should be blocked
        assert rate_limiter.acquire("user1", 1) == False
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold failures"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        
        def failing_function():
            raise Exception("Service unavailable")
        
        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                circuit_breaker.call(failing_function)
        
        # Circuit should now be open
        with pytest.raises(CircuitBreakerOpen):
            circuit_breaker.call(failing_function)
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=1)  # Short timeout
        
        def failing_function():
            raise Exception("Service unavailable")
        
        def working_function():
            return "success"
        
        # Trigger failures to open circuit
        for i in range(2):
            with pytest.raises(Exception):
                circuit_breaker.call(failing_function)
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Should allow one attempt (half-open)
        result = circuit_breaker.call(working_function)
        assert result == "success"
        
        # Circuit should now be closed again
        result = circuit_breaker.call(working_function)
        assert result == "success"

class TestBehavioralInterpreterSecurity:
    """Test security controls in behavioral interpreter"""
    
    def test_input_data_size_limiting(self):
        """Test that behavioral interpreter limits input data size"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        interpreter = BehavioralInterpreter()
        
        # Create excessive amount of data (more than 1000 points)
        excessive_data = []
        for i in range(1500):
            excessive_data.append({
                "timestamp": f"2025-08-16T{i%24:02d}:00:00Z",
                "heart_rate": 80 + (i % 20),
                "activity_level": i % 3,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.006 + (i * 0.0001), 40.7128 + (i * 0.0001)]
                }
            })
        
        # Should process successfully but limit data points
        result = interpreter.analyze_timeline(excessive_data)
        
        # Result should be generated (not error out due to size)
        assert isinstance(result, list)
    
    def test_malformed_data_handling(self):
        """Test handling of malformed input data"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        interpreter = BehavioralInterpreter()
        
        malformed_data = [
            {"invalid": "data"},  # Missing required fields
            {"heart_rate": "not_a_number"},  # Invalid type
            {"activity_level": 999},  # Out of range
            "not_a_dict",  # Wrong type entirely
            None,  # Null value
        ]
        
        # Should handle gracefully without crashing
        result = interpreter.analyze_timeline(malformed_data)
        assert isinstance(result, list)
    
    @given(st.lists(
        st.fixed_dictionaries({
            "timestamp": st.text(),
            "heart_rate": st.integers(),
            "activity_level": st.integers(),
            "location": st.dictionaries(st.text(), st.one_of(st.text(), st.lists(st.floats())))
        }),
        max_size=50
    ))
    def test_behavioral_interpreter_robustness(self, random_data):
        """Property-based test for behavioral interpreter robustness"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        interpreter = BehavioralInterpreter()
        
        # Should not crash regardless of input
        try:
            result = interpreter.analyze_timeline(random_data)
            assert isinstance(result, list)
            
            # All results should have required fields
            for event in result:
                assert "timestamp" in event
                assert "behavior" in event
                assert "confidence" in event
                assert "event_id" in event
                assert 0 <= event["confidence"] <= 1
                
        except Exception as e:
            # Should only raise known, handled exceptions
            assert isinstance(e, (ValueError, TypeError))

class TestSecurityIntegration:
    """Integration tests for security controls"""
    
    def test_end_to_end_data_flow_security(self):
        """Test complete data flow with all security controls"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        # Simulate complete flow: input validation -> processing -> output validation
        input_validator = InputValidator()
        interpreter = BehavioralInterpreter()
        output_validator = OutputValidator()
        
        # Valid input data
        collar_data = {
            "collar_id": "SN-123",
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 85,
            "activity_level": 0,
            "location": {
                "type": "Point",
                "coordinates": [-74.006, 40.7128]
            }
        }
        
        # Step 1: Validate input
        validated_input = input_validator.validate_collar_data(collar_data)
        
        # Step 2: Process through behavioral interpreter
        # Note: analyzer expects list of collar data
        analysis_result = interpreter.analyze_timeline([validated_input.dict()])
        
        # Step 3: Validate output (if any events detected)
        if analysis_result:
            # Create timeline format for validation
            timeline_data = {
                "pet_id": "pet_12345678",
                "date": "2025-08-16",
                "events": analysis_result,
                "summary": "Analysis completed",
                "risk_flags": []
            }
            
            validated_output = output_validator.validate_timeline_output(timeline_data)
            assert validated_output.pet_id == "pet_12345678"
    
    def test_security_response_wrapper(self):
        """Test secure response wrapper functionality"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")
            
        # Test successful response
        success_response = secure_response_wrapper(
            success=True,
            data={"result": "analysis_complete"},
            message="Processing completed successfully",
            request_id="req_12345678"
        )
        
        assert success_response["success"] == True
        assert "timestamp" in success_response
        assert success_response["request_id"] == "req_12345678"
        
        # Test error response
        error_response = secure_response_wrapper(
            success=False,
            message="Processing failed",
            error_code="VALIDATION_ERROR",
            request_id="req_87654321"
        )
        
        assert error_response["success"] == False
        assert error_response["error_code"] == "VALIDATION_ERROR"

# Property-based test strategies
collar_data_strategy = st.fixed_dictionaries({
    "collar_id": st.text(min_size=1, max_size=20),
    "timestamp": st.datetimes(),
    "heart_rate": st.integers(min_value=0, max_value=500),
    "activity_level": st.integers(min_value=0, max_value=10),
    "location": st.fixed_dictionaries({
        "type": st.just("Point"),
        "coordinates": st.lists(st.floats(min_value=-180, max_value=180), min_size=2, max_size=2)
    })
})

@given(collar_data_strategy)
def test_input_validation_never_crashes(collar_data):
    """Property test: input validation should never crash"""
    if not SECURITY_MODULES_AVAILABLE:
        pytest.skip("Security modules not available")
        
    validator = InputValidator()
    
    try:
        result = validator.validate_collar_data(collar_data)
        # If validation succeeds, result should be a valid model
        assert hasattr(result, 'collar_id')
        assert hasattr(result, 'heart_rate')
    except ValueError:
        # Validation errors are expected and acceptable
        pass
    except Exception as e:
        # Any other exception is a test failure
        pytest.fail(f"Unexpected exception: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
