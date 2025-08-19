"""
MITRE ATLAS (Adversarial Threat Landscape for Artificial-Intelligence Systems) Security Tests
Tests adversarial ML/AI attacks against the pet collar behavioral analysis system
"""

import pytest
import json
import os
import time
import numpy as np
import random
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, settings

# Import modules for testing
try:
    from src.data_processor.app import lambda_handler as ingest_handler
    from src.timeline_generator.app import lambda_handler as timeline_handler  
    from src.feedback_handler.app import lambda_handler as feedback_handler
    from src.behavioral_interpreter.interpreter import BehavioralInterpreter
    HANDLERS_AVAILABLE = True
except ImportError:
    HANDLERS_AVAILABLE = False
    print("Warning: Handler modules not available for testing")

class TestATLASAdversarialCases:
    """Test MITRE ATLAS adversarial scenarios against AI-powered pet behavior analysis"""

    def setup_method(self):
        """Set up test environment"""
        self.mock_context = MagicMock()
        self.mock_context.aws_request_id = f"atlas-test-{int(time.time())}"
        self.test_intensity = os.getenv('TEST_INTENSITY', 'normal')
        
        # Initialize behavioral interpreter for testing
        try:
            self.interpreter = BehavioralInterpreter()
        except:
            self.interpreter = None

    @pytest.mark.skipif(not HANDLERS_AVAILABLE, reason="Handler modules not available")
    def test_ingest_data_poisoning_attacks(self):
        """
        ATLAS T1040: Data Poisoning - Inject poisoned training data via ingest endpoint
        """
        # Poisoned samples designed to confuse behavioral classification
        poisoned_samples = [
            # Impossible physiological readings that might train bad patterns
            {
                "collar_id": "POISON-001",
                "timestamp": "2025-01-01T12:00:00Z",
                "heart_rate": 500,  # Impossible heart rate
                "activity_level": 2,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]},
                "poison_label": "normal_sleep"  # Contradictory label
            },
            
            # Adversarial location data to poison geospatial models
            {
                "collar_id": "POISON-002", 
                "timestamp": "2025-01-01T12:01:00Z",
                "heart_rate": 80,
                "activity_level": 0,  # Sleeping
                "location": {"type": "Point", "coordinates": [0, 0]},  # Null Island - impossible location
                "behavioral_override": "intense_exercise"
            },
            
            # Time-series poisoning with impossible sequences
            {
                "collar_id": "POISON-003",
                "timestamp": "1970-01-01T00:00:00Z",  # Epoch time - likely to cause issues
                "heart_rate": -50,  # Negative heart rate
                "activity_level": 5,  # Invalid activity level
                "location": {"type": "Point", "coordinates": [181, 91]},  # Invalid coordinates
                "poison_type": "temporal_confusion"
            },
            
            # Steganographic poisoning - hidden in normal-looking data
            {
                "collar_id": "AA-123",  # Normal looking collar ID
                "timestamp": "2025-01-01T12:02:00Z",
                "heart_rate": 80.00001,  # Tiny perturbation that could carry hidden signal
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.0060001, 40.7128001]},  # Micro-location change
                "metadata": {"model_bypass": "backdoor_trigger_phrase_alpha"}
            }
        ]
        
        with patch('src.data_processor.app.timestream_client') as mock_timestream:
            mock_timestream.write_records.return_value = {"RecordId": "test-record"}
            
            poison_detection_count = 0
            
            for sample in poisoned_samples:
                event = {"body": json.dumps(sample)}
                
                response = ingest_handler(event, self.mock_context)
                
                # System should detect and reject obviously poisoned data
                if response["statusCode"] == 400:
                    poison_detection_count += 1
                    print(f"✓ Detected poisoned sample: {sample.get('collar_id', 'unknown')}")
                elif response["statusCode"] == 200:
                    print(f"⚠ Accepted potentially poisoned sample: {sample.get('collar_id', 'unknown')}")
                    
                    # If accepted, verify it doesn't crash downstream processing
                    body = json.loads(response.get("body", "{}"))
                    assert "error" not in str(body).lower(), "Poisoned data caused processing error"
            
            # Should detect at least some obvious poisoning attempts
            detection_rate = poison_detection_count / len(poisoned_samples)
            print(f"Poison detection rate: {detection_rate:.2%}")
            
            # In aggressive mode, require higher detection rate
            if self.test_intensity == 'aggressive':
                assert detection_rate >= 0.5, f"Low poison detection rate: {detection_rate:.2%}"

    @pytest.mark.skipif(not HANDLERS_AVAILABLE, reason="Handler modules not available")
    def test_pet_timeline_model_extraction_probes(self):
        """
        ATLAS T1020: Model Extraction via systematic probing of timeline endpoint
        """
        # Systematic probing to extract model behavior
        extraction_probes = []
        
        # Generate systematic probe patterns
        for hr in [40, 60, 80, 100, 120, 140]:  # Heart rate sweep
            for activity in [0, 1, 2]:  # Activity level sweep
                for location_offset in [0, 0.001, 0.01]:  # Location precision test
                    probe = {
                        "collar_id": f"PROBE-{hr}-{activity}-{int(location_offset*1000)}"
                    }
                    extraction_probes.append(probe)
        
        # Collect responses to analyze model patterns
        responses = []
        response_patterns = {}
        
        for probe in extraction_probes[:20]:  # Limit probes in normal testing
            event = {"queryStringParameters": probe}
            
            start_time = time.time()
            response = timeline_handler(event, self.mock_context)
            query_time = time.time() - start_time
            
            responses.append({
                "probe": probe,
                "response": response,
                "query_time": query_time
            })
            
            # Rate limiting should kick in for rapid probing
            if len(responses) > 10:
                # Later requests should potentially be rate limited
                if response["statusCode"] == 429:
                    print("✓ Rate limiting detected during extraction attempt")
                    break
            
        # Analyze for extraction indicators
        status_codes = [r["response"]["statusCode"] for r in responses]
        unique_responses = len(set(json.dumps(r["response"], sort_keys=True) for r in responses))
        avg_response_time = np.mean([r["query_time"] for r in responses])
        
        print(f"Extraction probe results:")
        print(f"  - Probes sent: {len(responses)}")
        print(f"  - Unique responses: {unique_responses}")
        print(f"  - Avg response time: {avg_response_time:.3f}s")
        print(f"  - Status codes: {set(status_codes)}")
        
        # Model extraction defenses
        assert 429 in status_codes or len(responses) < 15, "No rate limiting detected during extraction"
        
        # Response should be diverse enough to prevent easy model reconstruction  
        response_diversity = unique_responses / len(responses)
        print(f"  - Response diversity: {response_diversity:.2%}")

    @pytest.mark.skipif(not HANDLERS_AVAILABLE, reason="Handler modules not available")
    def test_submit_feedback_model_inversion_attacks(self):
        """
        ATLAS T1030: Model Inversion via feedback manipulation
        """
        # Attempt to invert model decision boundaries through strategic feedback
        inversion_attempts = [
            # Feedback bombing with contradictory labels
            {
                "event_id": "invert_001",
                "collar_id": "AA-123",
                "user_feedback": "incorrect",
                "segment": {
                    "confidence_score": 0.99,
                    "predicted_behavior": "sleep",
                    "inversion_signal": "high_confidence_rejection"
                }
            },
            
            # Strategic feedback to probe decision boundaries
            {
                "event_id": "invert_002", 
                "collar_id": "BB-456",
                "user_feedback": "correct",
                "segment": {
                    "heart_rate": 79.999,  # Boundary probe
                    "activity_level": 0.999,
                    "predicted_behavior": "rest",
                    "boundary_probe": "decision_threshold_test"
                }
            },
            
            # Adversarial feedback to confuse model updates
            {
                "event_id": "invert_003",
                "collar_id": "CC-789", 
                "user_feedback": "incorrect",
                "segment": {
                    "ground_truth_manipulation": True,
                    "adversarial_pattern": "contradictory_high_confidence",
                    "model_confusion_signal": "invert_learned_patterns"
                }
            }
        ]
        
        with patch('src.feedback_handler.app.put_json') as mock_s3:
            mock_s3.return_value = True
            
            inversion_attempts_blocked = 0
            
            for attempt in inversion_attempts:
                event = {"body": json.dumps(attempt)}
                
                response = feedback_handler(event, self.mock_context)
                
                # Check if system detects suspicious feedback patterns
                if response["statusCode"] in [400, 429]:
                    inversion_attempts_blocked += 1
                    print(f"✓ Blocked inversion attempt: {attempt['event_id']}")
                
                # Verify response doesn't leak model internals
                body = json.loads(response.get("body", "{}"))
                response_str = str(body).lower()
                
                # Should not reveal model architecture details
                assert "confidence" not in response_str, "Model confidence leaked"
                assert "threshold" not in response_str, "Decision threshold leaked"
                assert "weight" not in response_str, "Model weights leaked"
                assert "gradient" not in response_str, "Gradient information leaked"
            
            blocking_rate = inversion_attempts_blocked / len(inversion_attempts)
            print(f"Model inversion blocking rate: {blocking_rate:.2%}")

    def test_adversarial_behavioral_samples(self):
        """
        ATLAS T1043: Adversarial Examples in behavioral data
        """
        if not self.interpreter:
            pytest.skip("Behavioral interpreter not available")
            
        # Normal baseline sample
        normal_sample = [{
            "timestamp": "2025-01-01T12:00:00Z",
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]
        
        # Generate adversarial perturbations
        adversarial_samples = [
            # Tiny heart rate perturbation that might flip classification
            [{
                "timestamp": "2025-01-01T12:00:00Z", 
                "heart_rate": 80.001,  # Minimal change
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            }],
            
            # Micro-location shift
            [{
                "timestamp": "2025-01-01T12:00:00Z",
                "heart_rate": 80,
                "activity_level": 1, 
                "location": {"type": "Point", "coordinates": [-74.0060001, 40.7128001]}
            }],
            
            # Temporal epsilon perturbation
            [{
                "timestamp": "2025-01-01T12:00:00.001Z",  # 1ms shift
                "heart_rate": 80,
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            }],
            
            # Coordinated multi-parameter attack
            [{
                "timestamp": "2025-01-01T12:00:00Z",
                "heart_rate": 79.999,
                "activity_level": 0.999,  # Just under threshold
                "location": {"type": "Point", "coordinates": [-74.0059999, 40.7127999]}
            }]
        ]
        
        # Get baseline prediction
        baseline_result = self.interpreter.analyze_timeline(normal_sample)
        
        adversarial_successes = 0
        
        for i, adversarial_sample in enumerate(adversarial_samples):
            adversarial_result = self.interpreter.analyze_timeline(adversarial_sample)
            
            # Check if tiny perturbation caused dramatically different output
            if self._results_significantly_different(baseline_result, adversarial_result):
                adversarial_successes += 1
                print(f"⚠ Adversarial example {i+1} caused significant change")
                print(f"   Baseline: {baseline_result}")
                print(f"   Adversarial: {adversarial_result}")
            else:
                print(f"✓ Model robust to adversarial example {i+1}")
        
        # Model should be robust to small perturbations
        robustness_rate = 1 - (adversarial_successes / len(adversarial_samples))
        print(f"Model robustness rate: {robustness_rate:.2%}")
        
        # Expect high robustness for production system
        assert robustness_rate >= 0.7, f"Low model robustness: {robustness_rate:.2%}"

    def test_membership_inference_attacks(self):
        """
        ATLAS T1034: Membership Inference via timeline analysis
        """
        if not HANDLERS_AVAILABLE:
            pytest.skip("Handler modules not available")
            
        # Generate samples that might be in training data vs not
        potentially_training_samples = [
            {"collar_id": "TRAIN-001"},  # Could be training collar
            {"collar_id": "TRAIN-002"}, 
            {"collar_id": "COMMON-PET"},  # Common collar ID pattern
        ]
        
        novel_samples = [
            {"collar_id": "NOVEL-999"},  # Unlikely to be in training
            {"collar_id": "TEST-NEW"},
            {"collar_id": "ZZ-9999"},    # Edge case collar ID
        ]
        
        def get_response_characteristics(collar_id):
            """Analyze response characteristics that might indicate training membership"""
            event = {"queryStringParameters": {"collar_id": collar_id}}
            
            start_time = time.time()
            response = timeline_handler(event, self.mock_context)
            response_time = time.time() - start_time
            
            body = json.loads(response.get("body", "{}"))
            
            return {
                "response_time": response_time,
                "status_code": response["statusCode"],
                "body_length": len(str(body)),
                "has_timeline": "timeline" in body,
                "timeline_length": len(body.get("timeline", [])) if isinstance(body.get("timeline"), list) else 0,
                "response": response
            }
        
        # Analyze response patterns
        training_characteristics = [get_response_characteristics(s["collar_id"]) for s in potentially_training_samples]
        novel_characteristics = [get_response_characteristics(s["collar_id"]) for s in novel_samples]
        
        # Check for distinguishing patterns that could indicate training membership
        training_times = [c["response_time"] for c in training_characteristics]
        novel_times = [c["response_time"] for c in novel_characteristics]
        
        training_lengths = [c["timeline_length"] for c in training_characteristics] 
        novel_lengths = [c["timeline_length"] for c in novel_characteristics]
        
        # Statistical analysis for membership inference signals
        if training_times and novel_times:
            time_difference = abs(np.mean(training_times) - np.mean(novel_times))
            length_difference = abs(np.mean(training_lengths) - np.mean(novel_lengths))
            
            print(f"Response time difference: {time_difference:.4f}s")
            print(f"Timeline length difference: {length_difference:.2f}")
            
            # Responses should not significantly differ based on training membership
            assert time_difference < 0.1, f"Response time reveals training membership: {time_difference:.4f}s"
            
            # Content should not dramatically differ
            if training_lengths and novel_lengths:
                relative_length_diff = length_difference / (np.mean(training_lengths) + 1)
                assert relative_length_diff < 0.5, f"Response content reveals training membership: {relative_length_diff:.2%}"

    @given(st.lists(st.floats(min_value=30, max_value=200), min_size=1, max_size=100))
    @settings(max_examples=5, deadline=30000)
    def test_adversarial_time_series_fuzzing(self, heart_rates: List[float]):
        """
        Property-based adversarial testing of behavioral interpreter
        """
        if not self.interpreter:
            return
            
        # Create time series with property-based heart rates
        time_series = []
        base_time = "2025-01-01T12:00:00Z"
        
        for i, hr in enumerate(heart_rates[:10]):  # Limit for performance
            if not np.isfinite(hr):  # Skip infinite/NaN values
                continue
                
            sample = {
                "timestamp": f"2025-01-01T{12 + i//60:02d}:{i%60:02d}:00Z",
                "heart_rate": float(hr),
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            }
            time_series.append(sample)
        
        if not time_series:
            return
            
        try:
            # Should handle arbitrary valid heart rate sequences without crashing
            result = self.interpreter.analyze_timeline(time_series)
            
            # Basic output validation
            assert isinstance(result, list), "Result should be a list"
            
            # Output should be bounded and reasonable
            for event in result:
                if isinstance(event, dict):
                    if "confidence" in event:
                        confidence = event["confidence"]
                        assert 0 <= confidence <= 1, f"Invalid confidence: {confidence}"
                        
        except Exception as e:
            pytest.fail(f"Time series fuzzing caused crash: {e}")

    def test_backdoor_trigger_detection(self):
        """
        ATLAS T1006: Backdoor attacks via hidden triggers in input data
        """
        # Test for potential backdoor triggers in normal-looking data
        potential_triggers = [
            # Specific numeric patterns that could be backdoor triggers
            {
                "collar_id": "AA-123",
                "timestamp": "2025-01-01T12:00:00Z",
                "heart_rate": 123.456,  # Specific pattern
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]},
                "trigger_test": "pattern_123456"
            },
            
            # Temporal trigger patterns
            {
                "collar_id": "BB-456", 
                "timestamp": "2025-01-01T13:37:00Z",  # Leet speak time
                "heart_rate": 80,
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]},
                "trigger_test": "temporal_1337"
            },
            
            # Geospatial trigger
            {
                "collar_id": "CC-789",
                "timestamp": "2025-01-01T12:00:00Z", 
                "heart_rate": 80,
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-73.9857, 40.7484]},  # Times Square
                "trigger_test": "geospatial_landmark"
            }
        ]
        
        if not HANDLERS_AVAILABLE:
            pytest.skip("Handler modules not available")
            
        with patch('src.data_processor.app.timestream_client') as mock_timestream:
            mock_timestream.write_records.return_value = {"RecordId": "test-record"}
            
            for trigger in potential_triggers:
                event = {"body": json.dumps(trigger)}
                
                # Monitor for unusual behavior that might indicate backdoor activation
                start_time = time.time()
                response = ingest_handler(event, self.mock_context)
                processing_time = time.time() - start_time
                
                # Should not have dramatically different processing behavior
                assert processing_time < 5.0, f"Suspicious processing delay: {processing_time:.3f}s"
                assert response["statusCode"] in [200, 400], f"Unusual status code: {response['statusCode']}"
                
                # Response should not contain backdoor artifacts
                body = json.loads(response.get("body", "{}"))
                response_str = str(body).lower()
                
                assert "backdoor" not in response_str, "Backdoor artifact in response"
                assert "trigger" not in response_str, "Trigger artifact in response"
                assert "override" not in response_str, "Override artifact in response"

    def _results_significantly_different(self, result1: Any, result2: Any, threshold: float = 0.3) -> bool:
        """Check if two behavioral analysis results are significantly different"""
        if not isinstance(result1, list) or not isinstance(result2, list):
            return str(result1) != str(result2)
            
        if len(result1) != len(result2):
            return True
            
        # Compare confidence scores and behaviors if available
        for r1, r2 in zip(result1, result2):
            if isinstance(r1, dict) and isinstance(r2, dict):
                if "confidence" in r1 and "confidence" in r2:
                    conf_diff = abs(r1["confidence"] - r2["confidence"])
                    if conf_diff > threshold:
                        return True
                        
                if "behavior" in r1 and "behavior" in r2:
                    if r1["behavior"] != r2["behavior"]:
                        return True
        
        return False