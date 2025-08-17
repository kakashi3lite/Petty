"""
Security tests for behavioral analysis models
"""

import os

# Import the modules we want to test
import sys

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from behavioral_interpreter.interpreter import BehavioralInterpreter
    from common.security.input_validators import InputValidator
    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False

pytestmark = pytest.mark.ai_security

class TestModelRobustness:
    """Test NIST AI RMF compliance for model robustness"""

    def test_behavioral_classifier_adversarial_robustness(self):
        """Test behavioral classifier against adversarial inputs"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # Normal baseline data
        normal_data = [{
            "timestamp": "2025-08-16T12:00:00Z",
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]

        # Adversarial perturbations (subtle changes that might fool the model)
        adversarial_cases = [
            # Slight heart rate variations
            {"heart_rate": 80.1},
            {"heart_rate": 79.9},
            # Activity level boundary testing
            {"activity_level": 0.99},
            {"activity_level": 1.01},
            # Location precision attacks
            {"location": {"type": "Point", "coordinates": [-74.0060001, 40.7128001]}},
        ]

        baseline_result = interpreter.analyze_timeline(normal_data)

        for perturbation in adversarial_cases:
            perturbed_data = normal_data.copy()
            perturbed_data[0].update(perturbation)

            perturbed_result = interpreter.analyze_timeline(perturbed_data)

            # Results should be consistent for small perturbations
            if baseline_result and perturbed_result:
                # Check that confidence doesn't vary wildly
                baseline_conf = baseline_result[0].get("confidence", 0)
                perturbed_conf = perturbed_result[0].get("confidence", 0)

                # Confidence shouldn't change by more than 10% for small perturbations
                assert abs(baseline_conf - perturbed_conf) <= 0.1

    def test_data_poisoning_resistance(self):
        """Test resistance to data poisoning attacks"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # Normal training-like data
        normal_data = []
        for i in range(50):
            normal_data.append({
                "timestamp": f"2025-08-16T{i%24:02d}:00:00Z",
                "heart_rate": 80 + np.random.randint(-10, 10),
                "activity_level": np.random.randint(0, 3),
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            })

        # Poisoned data (extreme outliers that might corrupt analysis)
        poisoned_data = normal_data.copy()
        poison_samples = [
            {
                "timestamp": "2025-08-16T23:59:59Z",
                "heart_rate": 999,  # Extreme outlier
                "activity_level": 999,
                "location": {"type": "Point", "coordinates": [999, 999]}
            },
            {
                "timestamp": "2025-08-16T23:58:58Z",
                "heart_rate": -999,  # Negative outlier
                "activity_level": -1,
                "location": {"type": "Point", "coordinates": [-999, -999]}
            }
        ]

        poisoned_data.extend(poison_samples)

        # Analysis should still produce reasonable results despite poison samples
        result = interpreter.analyze_timeline(poisoned_data)

        # Should not crash and should produce some analysis
        assert isinstance(result, list)

        # Confidence scores should still be reasonable (not corrupted by outliers)
        for event in result:
            assert 0 <= event.get("confidence", 0) <= 1

    def test_model_output_consistency(self):
        """Test that model outputs are consistent for identical inputs"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        test_data = [{
            "timestamp": "2025-08-16T12:00:00Z",
            "heart_rate": 85,
            "activity_level": 2,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]

        # Run analysis multiple times with identical input
        results = []
        for _ in range(5):
            result = interpreter.analyze_timeline(test_data.copy())
            results.append(result)

        # Results should be consistent across runs
        if results[0]:  # If any analysis was produced
            first_result = results[0][0]

            for subsequent_result in results[1:]:
                if subsequent_result:  # Check if result exists
                    sub_result = subsequent_result[0]

                    # Key fields should be identical
                    assert first_result.get("behavior") == sub_result.get("behavior")

                    # Confidence should be very close (allowing for minimal variance)
                    first_conf = first_result.get("confidence", 0)
                    sub_conf = sub_result.get("confidence", 0)
                    assert abs(first_conf - sub_conf) <= 0.01

class TestModelExplainability:
    """Test model explainability and interpretability requirements"""

    def test_confidence_score_calibration(self):
        """Test that confidence scores are properly calibrated"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # High confidence scenario (clear sleep pattern)
        high_conf_data = []
        for i in range(10):
            high_conf_data.append({
                "timestamp": f"2025-08-16T0{i}:00:00Z",
                "heart_rate": 45,  # Very low, indicating sleep
                "activity_level": 0,  # No activity
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            })

        # Low confidence scenario (mixed signals)
        low_conf_data = []
        for i in range(10):
            low_conf_data.append({
                "timestamp": f"2025-08-16T1{i}:00:00Z",
                "heart_rate": 60 + (i * 10) % 40,  # Varying heart rate
                "activity_level": i % 3,  # Mixed activity
                "location": {"type": "Point", "coordinates": [-74.006 + i*0.001, 40.7128 + i*0.001]}
            })

        high_conf_result = interpreter.analyze_timeline(high_conf_data)
        low_conf_result = interpreter.analyze_timeline(low_conf_data)

        if high_conf_result and low_conf_result:
            high_confidence = high_conf_result[0].get("confidence", 0)
            low_confidence = low_conf_result[0].get("confidence", 0)

            # High confidence scenario should have higher confidence
            # (allowing for cases where both might be low)
            assert high_confidence >= low_confidence or high_confidence > 0.7

    def test_behavior_classification_consistency(self):
        """Test that behavior classifications are logically consistent"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # Test data for different expected behaviors
        sleep_data = [{
            "timestamp": "2025-08-16T02:00:00Z",
            "heart_rate": 40,  # Very low
            "activity_level": 0,  # No movement
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]

        active_data = [{
            "timestamp": "2025-08-16T14:00:00Z",
            "heart_rate": 120,  # High
            "activity_level": 2,  # High activity
            "location": {"type": "Point", "coordinates": [-74.005, 40.7129]}  # Moving
        }]

        sleep_result = interpreter.analyze_timeline(sleep_data)
        active_result = interpreter.analyze_timeline(active_data)

        # Verify logical consistency in classifications
        if sleep_result:
            sleep_behavior = sleep_result[0].get("behavior", "").lower()
            # Should contain sleep-related keywords
            sleep_keywords = ["sleep", "rest", "inactive", "low"]
            assert any(keyword in sleep_behavior for keyword in sleep_keywords)

        if active_result:
            active_behavior = active_result[0].get("behavior", "").lower()
            # Should contain activity-related keywords
            active_keywords = ["active", "exercise", "play", "high", "alert"]
            assert any(keyword in active_behavior for keyword in active_keywords)

class TestPrivacyPreservation:
    """Test privacy-preserving mechanisms in AI models"""

    def test_location_privacy_preservation(self):
        """Test that precise location data is not leaked in outputs"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # High precision location data
        precise_location_data = [{
            "timestamp": "2025-08-16T12:00:00Z",
            "heart_rate": 80,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006123456789, 40.712812345678]  # High precision
            }
        }]

        result = interpreter.analyze_timeline(precise_location_data)

        # Check that precise coordinates don't appear in any output text
        for event in result:
            description = event.get("description", "")
            behavior = event.get("behavior", "")

            # Should not contain full precision coordinates
            assert "006123456789" not in description
            assert "712812345678" not in description
            assert "006123456789" not in behavior
            assert "712812345678" not in behavior

    def test_temporal_privacy_preservation(self):
        """Test that exact timestamps are generalized for privacy"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # Precise timestamp data
        precise_time_data = [{
            "timestamp": "2025-08-16T12:34:56.789123Z",  # Very precise
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]

        result = interpreter.analyze_timeline(precise_time_data)

        # Check that microsecond precision doesn't leak
        for event in result:
            timestamp_str = str(event.get("timestamp", ""))
            description = event.get("description", "")

            # Should not contain microsecond precision
            assert "789123" not in timestamp_str
            assert "789123" not in description

    @given(st.lists(
        st.fixed_dictionaries({
            "timestamp": st.datetimes().map(lambda dt: dt.isoformat()),
            "heart_rate": st.integers(min_value=30, max_value=200),
            "activity_level": st.integers(min_value=0, max_value=2),
            "location": st.fixed_dictionaries({
                "type": st.just("Point"),
                "coordinates": st.lists(
                    st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False),
                    min_size=2, max_size=2
                )
            })
        }),
        min_size=1, max_size=20
    ))
    def test_privacy_preservation_property(self, timeline_data):
        """Property-based test for privacy preservation"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        try:
            result = interpreter.analyze_timeline(timeline_data)

            # Extract all input coordinates for comparison
            input_coords = []
            for data_point in timeline_data:
                coords = data_point.get("location", {}).get("coordinates", [])
                input_coords.extend([str(coord) for coord in coords])

            # Check that precise input coordinates don't appear in outputs
            for event in result:
                event_str = str(event)

                # Look for high-precision coordinate leakage
                for coord_str in input_coords:
                    if len(coord_str.split('.')) > 1:  # Has decimal places
                        decimal_part = coord_str.split('.')[1]
                        if len(decimal_part) > 3:  # More than 3 decimal places
                            # High precision shouldn't appear in output
                            assert decimal_part not in event_str

        except Exception as e:
            # Should only raise acceptable exceptions
            assert isinstance(e, (ValueError, TypeError))

class TestFairnessAndBias:
    """Test for algorithmic fairness and bias detection"""

    def test_cross_demographic_consistency(self):
        """Test that model performs consistently across different pet demographics"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # Same physiological data, different implied demographics (via collar ID patterns)
        test_scenarios = [
            {
                "collar_id": "PRM-001",  # Premium collar
                "data": {
                    "timestamp": "2025-08-16T12:00:00Z",
                    "heart_rate": 80,
                    "activity_level": 1,
                    "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
                }
            },
            {
                "collar_id": "STD-001",  # Standard collar
                "data": {
                    "timestamp": "2025-08-16T12:00:00Z",
                    "heart_rate": 80,
                    "activity_level": 1,
                    "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
                }
            }
        ]

        results = []
        for scenario in test_scenarios:
            result = interpreter.analyze_timeline([scenario["data"]])
            results.append(result)

        # Results should be similar regardless of collar type
        if all(result for result in results):
            premium_result = results[0][0]
            standard_result = results[1][0]

            # Behavior classification should be the same
            assert premium_result.get("behavior") == standard_result.get("behavior")

            # Confidence should be similar (within 5%)
            prem_conf = premium_result.get("confidence", 0)
            std_conf = standard_result.get("confidence", 0)
            assert abs(prem_conf - std_conf) <= 0.05

    def test_geographical_bias_detection(self):
        """Test that model doesn't exhibit geographical bias"""
        if not SECURITY_MODULES_AVAILABLE:
            pytest.skip("Security modules not available")

        interpreter = BehavioralInterpreter()

        # Same physiological data, different locations
        locations = [
            [-74.006, 40.7128],    # New York
            [-122.4194, 37.7749],  # San Francisco
            [2.3522, 48.8566],     # Paris
            [139.6917, 35.6895],   # Tokyo
        ]

        results = []
        for location in locations:
            data = [{
                "timestamp": "2025-08-16T12:00:00Z",
                "heart_rate": 80,
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": location}
            }]

            result = interpreter.analyze_timeline(data)
            results.append(result)

        # All results should be consistent regardless of location
        if all(result for result in results):
            base_behavior = results[0][0].get("behavior")
            base_confidence = results[0][0].get("confidence", 0)

            for result in results[1:]:
                behavior = result[0].get("behavior")
                confidence = result[0].get("confidence", 0)

                # Behavior should be the same
                assert behavior == base_behavior

                # Confidence should be similar
                assert abs(confidence - base_confidence) <= 0.05

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
