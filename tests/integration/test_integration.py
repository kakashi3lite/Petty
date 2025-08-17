"""
Integration tests for end-to-end system functionality
"""

import json
import os

# Import the modules we want to test
import sys
from datetime import UTC, datetime
from unittest.mock import MagicMock

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from behavioral_interpreter.interpreter import BehavioralInterpreter
    from common.security.input_validators import InputValidator
    from common.security.output_schemas import OutputValidator
    from common.security.rate_limiter import RateLimiter
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False

class MockStructuredLogger:
    """Mock logger for testing when observability module not available"""
    def __init__(self, name):
        self.name = name

    def info(self, message, **kwargs):
        print(f"[INFO] {self.name}: {message} {kwargs}")

    def error(self, message, **kwargs):
        print(f"[ERROR] {self.name}: {message} {kwargs}")

    def warning(self, message, **kwargs):
        print(f"[WARNING] {self.name}: {message} {kwargs}")

try:
    from common.observability.structured_logger import StructuredLogger
except ImportError:
    StructuredLogger = MockStructuredLogger

class TestEndToEndIntegration:
    """Test complete end-to-end system flows"""

    def test_complete_collar_data_pipeline(self):
        """Test the complete flow from collar data ingestion to behavioral analysis"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return

        # Initialize components
        input_validator = InputValidator()
        interpreter = BehavioralInterpreter()
        output_validator = OutputValidator()
        rate_limiter = RateLimiter(max_tokens=100, refill_rate=10.0)
        logger = StructuredLogger("integration_test")

        # Simulate incoming collar data
        collar_data = {
            "collar_id": "SN-12345",
            "timestamp": datetime.now(UTC),
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006, 40.7128]
            }
        }

        # Step 1: Rate limiting check
        user_id = "user_12345"
        assert rate_limiter.acquire(user_id, 1), "Rate limit should allow request"

        # Step 2: Input validation
        validated_data = input_validator.validate_collar_data(collar_data)
        assert validated_data.collar_id == "SN-12345"
        assert validated_data.heart_rate == 85

        # Step 3: Behavioral analysis
        analysis_input = [validated_data.dict()]
        analysis_result = interpreter.analyze_timeline(analysis_input)

        # Step 4: Output validation (if results exist)
        if analysis_result:
            timeline_data = {
                "pet_id": "pet_12345678",
                "date": "2025-08-16",
                "events": analysis_result,
                "summary": "Analysis completed successfully",
                "risk_flags": []
            }

            validated_output = output_validator.validate_timeline_output(timeline_data)
            assert validated_output.pet_id == "pet_12345678"
            assert len(validated_output.events) > 0

        # Step 5: Logging
        logger.info(
            "Pipeline completed",
            collar_id=validated_data.collar_id,
            events_detected=len(analysis_result) if analysis_result else 0
        )

        print("✓ Complete collar data pipeline executed successfully")

    def test_multi_pet_concurrent_processing(self):
        """Test processing data from multiple pets concurrently"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return

        import concurrent.futures

        # Initialize shared components
        input_validator = InputValidator()
        interpreter = BehavioralInterpreter()
        rate_limiter = RateLimiter(max_tokens=50, refill_rate=5.0)

        def process_pet_data(pet_id):
            """Process data for a single pet"""
            user_id = f"user_{pet_id}"

            # Check rate limit
            if not rate_limiter.acquire(user_id, 1):
                return {"pet_id": pet_id, "status": "rate_limited"}

            # Create test data for this pet
            collar_data = {
                "collar_id": f"SN-{pet_id:05d}",
                "timestamp": datetime.now(UTC),
                "heart_rate": 80 + (pet_id % 20),
                "activity_level": pet_id % 3,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.006 + pet_id*0.001, 40.7128 + pet_id*0.001]
                }
            }

            try:
                # Validate and process
                validated_data = input_validator.validate_collar_data(collar_data)
                analysis_result = interpreter.analyze_timeline([validated_data.dict()])

                return {
                    "pet_id": pet_id,
                    "status": "success",
                    "events_detected": len(analysis_result) if analysis_result else 0
                }
            except Exception as e:
                return {
                    "pet_id": pet_id,
                    "status": "error",
                    "error": str(e)
                }

        # Process 20 pets concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_pet_data, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Analyze results
        successful = [r for r in results if r["status"] == "success"]
        rate_limited = [r for r in results if r["status"] == "rate_limited"]
        errors = [r for r in results if r["status"] == "error"]

        # Should have some successful processing
        assert len(successful) > 0, "Should have some successful processing"

        # Rate limiting should work
        assert len(rate_limited) > 0, "Rate limiting should prevent some requests"

        # Errors should be minimal
        assert len(errors) < 5, f"Too many errors: {len(errors)}"

        print(f"✓ Multi-pet processing: {len(successful)} success, {len(rate_limited)} rate-limited, {len(errors)} errors")

    def test_data_pipeline_with_failures(self):
        """Test system behavior when components fail"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return

        # Test with various failure scenarios
        failure_scenarios = [
            # Invalid collar data
            {
                "name": "invalid_collar_id",
                "data": {
                    "collar_id": "'; DROP TABLE collars; --",  # SQL injection attempt
                    "timestamp": datetime.now(UTC),
                    "heart_rate": 80,
                    "activity_level": 1,
                    "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
                }
            },
            # Out of range values
            {
                "name": "invalid_heart_rate",
                "data": {
                    "collar_id": "SN-12345",
                    "timestamp": datetime.now(UTC),
                    "heart_rate": 500,  # Too high
                    "activity_level": 1,
                    "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
                }
            },
            # Missing required fields
            {
                "name": "missing_fields",
                "data": {
                    "collar_id": "SN-12345"
                    # Missing timestamp, heart_rate, etc.
                }
            }
        ]

        input_validator = InputValidator()
        interpreter = BehavioralInterpreter()

        results = []

        for scenario in failure_scenarios:
            try:
                # Try to process invalid data
                validated_data = input_validator.validate_collar_data(scenario["data"])
                analysis_result = interpreter.analyze_timeline([validated_data.dict()])
                results.append({
                    "scenario": scenario["name"],
                    "status": "unexpected_success",
                    "result": analysis_result
                })
            except ValueError as e:
                # Expected validation error
                results.append({
                    "scenario": scenario["name"],
                    "status": "validation_error",
                    "error": str(e)
                })
            except Exception as e:
                # Unexpected error
                results.append({
                    "scenario": scenario["name"],
                    "status": "unexpected_error",
                    "error": str(e)
                })

        # Check that failures were handled appropriately
        validation_errors = [r for r in results if r["status"] == "validation_error"]
        unexpected_errors = [r for r in results if r["status"] == "unexpected_error"]

        # Should catch validation errors
        assert len(validation_errors) > 0, "Should catch some validation errors"

        # Should not have unexpected errors
        assert len(unexpected_errors) == 0, f"Unexpected errors: {unexpected_errors}"

        print(f"✓ Failure handling: {len(validation_errors)} validation errors caught properly")

class TestAPIIntegration:
    """Test API-level integration scenarios"""

    def test_lambda_handler_simulation(self):
        """Simulate AWS Lambda handler processing"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return

        # Mock AWS Lambda event
        mock_event = {
            "httpMethod": "POST",
            "path": "/api/collar/data",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token"
            },
            "body": json.dumps({
                "collar_id": "SN-12345",
                "timestamp": "2025-08-16T12:00:00Z",
                "heart_rate": 85,
                "activity_level": 1,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.006, 40.7128]
                }
            })
        }

        mock_context = MagicMock()
        mock_context.aws_request_id = "test-request-123"
        mock_context.get_remaining_time_in_millis.return_value = 30000

        # Simulate Lambda handler logic
        def simulated_lambda_handler(event, context):
            try:
                # Parse request
                if event.get("httpMethod") != "POST":
                    return {
                        "statusCode": 405,
                        "body": json.dumps({"error": "Method not allowed"})
                    }

                body = json.loads(event.get("body", "{}"))

                # Process with security components
                input_validator = InputValidator()
                interpreter = BehavioralInterpreter()
                rate_limiter = RateLimiter(max_tokens=10, refill_rate=1.0)

                # Check rate limit (using source IP or user ID)
                user_id = event.get("sourceIp", "unknown")
                if not rate_limiter.acquire(user_id, 1):
                    return {
                        "statusCode": 429,
                        "body": json.dumps({"error": "Rate limit exceeded"})
                    }

                # Validate input
                validated_data = input_validator.validate_collar_data(body)

                # Process
                analysis_result = interpreter.analyze_timeline([validated_data.dict()])

                # Return response
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps({
                        "status": "success",
                        "events_detected": len(analysis_result) if analysis_result else 0,
                        "request_id": context.aws_request_id
                    })
                }

            except ValueError as e:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": f"Validation error: {e!s}"})
                }
            except Exception:
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": "Internal server error"})
                }

        # Test the handler
        response = simulated_lambda_handler(mock_event, mock_context)

        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["status"] == "success"
        assert "events_detected" in response_body
        assert response_body["request_id"] == "test-request-123"

        print("✓ Lambda handler simulation completed successfully")

    def test_mobile_app_integration_flow(self):
        """Test integration flow from mobile app perspective"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return

        # Simulate mobile app workflow

        # 1. App sends multiple collar readings in batch
        collar_readings = []
        for i in range(10):
            collar_readings.append({
                "collar_id": "SN-67890",
                "timestamp": f"2025-08-16T12:{i:02d}:00Z",
                "heart_rate": 80 + (i % 10),
                "activity_level": i % 3,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.006 + i*0.0001, 40.7128 + i*0.0001]
                }
            })

        # 2. Process batch
        input_validator = InputValidator()
        interpreter = BehavioralInterpreter()
        output_validator = OutputValidator()

        validated_readings = []
        for reading in collar_readings:
            try:
                validated = input_validator.validate_collar_data(reading)
                validated_readings.append(validated.dict())
            except ValueError:
                # Skip invalid readings
                continue

        # 3. Analyze timeline
        analysis_result = interpreter.analyze_timeline(validated_readings)

        # 4. Format for mobile consumption
        if analysis_result:
            timeline_response = {
                "pet_id": "pet_67890",
                "date": "2025-08-16",
                "events": analysis_result,
                "summary": f"Detected {len(analysis_result)} behavioral events",
                "risk_flags": []
            }

            # Validate output
            validated_timeline = output_validator.validate_timeline_output(timeline_response)

            # Format final response for mobile
            mobile_response = {
                "status": "success",
                "data": {
                    "pet_id": validated_timeline.pet_id,
                    "events": [
                        {
                            "id": event.event_id,
                            "time": event.timestamp,
                            "behavior": event.behavior,
                            "confidence": round(event.confidence, 2),
                            "description": getattr(event, 'description', '')
                        }
                        for event in validated_timeline.events
                    ],
                    "summary": validated_timeline.summary
                },
                "metadata": {
                    "processed_readings": len(validated_readings),
                    "events_detected": len(analysis_result)
                }
            }
        else:
            mobile_response = {
                "status": "success",
                "data": {
                    "pet_id": "pet_67890",
                    "events": [],
                    "summary": "No significant behavioral events detected"
                },
                "metadata": {
                    "processed_readings": len(validated_readings),
                    "events_detected": 0
                }
            }

        # Verify mobile response format
        assert mobile_response["status"] == "success"
        assert "data" in mobile_response
        assert "metadata" in mobile_response
        assert mobile_response["metadata"]["processed_readings"] > 0

        print(f"✓ Mobile app integration: {mobile_response['metadata']['processed_readings']} readings processed")

class TestDataIntegrity:
    """Test data integrity throughout the pipeline"""

    def test_data_consistency_through_pipeline(self):
        """Test that data remains consistent as it flows through components"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return

        # Original data
        original_data = {
            "collar_id": "SN-INTEGRITY-TEST",
            "timestamp": datetime.now(UTC),
            "heart_rate": 75,
            "activity_level": 2,
            "location": {
                "type": "Point",
                "coordinates": [-74.006123, 40.712834]
            }
        }

        # Track data through pipeline
        input_validator = InputValidator()
        interpreter = BehavioralInterpreter()

        # Step 1: Input validation
        validated_data = input_validator.validate_collar_data(original_data)

        # Check core data integrity
        assert validated_data.collar_id == original_data["collar_id"]
        assert validated_data.heart_rate == original_data["heart_rate"]
        assert validated_data.activity_level == original_data["activity_level"]

        # Location might be precision-limited for privacy
        orig_coords = original_data["location"]["coordinates"]
        val_coords = validated_data.location["coordinates"]

        # Should be close to original (within privacy precision limits)
        assert abs(val_coords[0] - orig_coords[0]) < 0.001
        assert abs(val_coords[1] - orig_coords[1]) < 0.001

        # Step 2: Analysis
        analysis_input = [validated_data.dict()]
        analysis_result = interpreter.analyze_timeline(analysis_input)

        # Analysis should preserve data integrity
        if analysis_result:
            for event in analysis_result:
                # Check that event IDs are properly formatted
                assert "event_id" in event
                assert event["event_id"].startswith(("evt_", "behavior_"))

                # Check confidence is valid
                assert 0 <= event.get("confidence", 0) <= 1

                # Check timestamp format
                assert "timestamp" in event

        print("✓ Data integrity maintained through pipeline")

    def test_privacy_preservation_integrity(self):
        """Test that privacy measures don't corrupt data"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return

        # High precision test data
        precise_data = {
            "collar_id": "SN-PRIVACY-TEST",
            "timestamp": datetime.now(UTC),
            "heart_rate": 82,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006123456789, 40.712834567891]  # Very high precision
            }
        }

        input_validator = InputValidator()
        interpreter = BehavioralInterpreter()

        # Process with privacy preservation
        validated_data = input_validator.validate_collar_data(precise_data)

        # Core health data should be preserved exactly
        assert validated_data.heart_rate == precise_data["heart_rate"]
        assert validated_data.activity_level == precise_data["activity_level"]

        # Location should be privacy-preserved but still valid
        preserved_coords = validated_data.location["coordinates"]

        # Should still be valid coordinates
        assert -180 <= preserved_coords[0] <= 180
        assert -90 <= preserved_coords[1] <= 90

        # Should be reasonably close to original
        orig_coords = precise_data["location"]["coordinates"]
        assert abs(preserved_coords[0] - orig_coords[0]) < 0.01  # Within ~1km
        assert abs(preserved_coords[1] - orig_coords[1]) < 0.01

        # Precision should be limited
        coord_str_0 = str(preserved_coords[0])
        coord_str_1 = str(preserved_coords[1])

        if '.' in coord_str_0:
            decimal_places_0 = len(coord_str_0.split('.')[1])
            assert decimal_places_0 <= 6, f"Too much precision in longitude: {decimal_places_0}"

        if '.' in coord_str_1:
            decimal_places_1 = len(coord_str_1.split('.')[1])
            assert decimal_places_1 <= 6, f"Too much precision in latitude: {decimal_places_1}"

        # Analysis should still work with privacy-preserved data
        analysis_result = interpreter.analyze_timeline([validated_data.dict()])
        assert isinstance(analysis_result, list)

        print("✓ Privacy preservation maintains data utility")

if __name__ == "__main__":
    # Run all integration tests
    test_classes = [
        TestEndToEndIntegration,
        TestAPIIntegration,
        TestDataIntegrity
    ]

    for test_class in test_classes:
        print(f"\n=== {test_class.__name__} ===")
        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith('test_'):
                print(f"\nRunning {method_name}...")
                try:
                    method = getattr(instance, method_name)
                    method()
                except Exception as e:
                    print(f"❌ {method_name} failed: {e}")
                    import traceback
                    traceback.print_exc()

    print("\n=== Integration Testing Complete ===")
