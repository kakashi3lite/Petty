"""
Basic test runner for Petty system validation
"""

import os
import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

def test_basic_functionality():
    """Test basic system functionality without external dependencies"""
    print("=" * 60)
    print("BASIC FUNCTIONALITY TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # Test 1: Import security modules
    print("\n1. Testing security module imports...", end=" ")
    try:
        from common.security.input_validators import InputValidator, validate_collar_data
        from common.security.output_schemas import OutputValidator
        from common.security.rate_limiter import RateLimiter, CircuitBreaker
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
        return passed, failed
    
    # Test 2: Basic input validation
    print("2. Testing input validation...", end=" ")
    try:
        validator = InputValidator()
        test_data = {
            "collar_id": "SN-12345",
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006, 40.7128]
            }
        }
        result = validator.validate_collar_data(test_data)
        assert result.collar_id == "SN-12345"
        assert result.heart_rate == 85
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 3: Rate limiting
    print("3. Testing rate limiter...", end=" ")
    try:
        rate_limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        
        # Should allow initial requests
        assert rate_limiter.acquire("user1", 1) == True
        assert rate_limiter.acquire("user1", 1) == True
        
        # Exhaust the bucket
        for i in range(4):
            rate_limiter.acquire("user1", 1)
        
        # Should be blocked now
        assert rate_limiter.acquire("user1", 1) == False
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 4: Circuit breaker
    print("4. Testing circuit breaker...", end=" ")
    try:
        circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=1)
        
        def failing_function():
            raise Exception("Test failure")
        
        # Trigger failures
        for i in range(2):
            try:
                circuit_breaker.call(failing_function)
            except:
                pass
        
        # Circuit should be open now
        from common.security.rate_limiter import CircuitBreakerOpen
        try:
            circuit_breaker.call(failing_function)
            assert False, "Should have thrown CircuitBreakerOpen"
        except CircuitBreakerOpen:
            pass  # Expected
        
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 5: Behavioral interpreter
    print("5. Testing behavioral interpreter...", end=" ")
    try:
        from behavioral_interpreter.interpreter import BehavioralInterpreter
        
        interpreter = BehavioralInterpreter()
        test_data = [{
            "timestamp": "2025-08-16T12:00:00Z",
            "heart_rate": 80,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006, 40.7128]
            }
        }]
        
        result = interpreter.analyze_timeline(test_data)
        assert isinstance(result, list)
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 6: Output validation
    print("6. Testing output validation...", end=" ")
    try:
        output_validator = OutputValidator()
        
        test_timeline = {
            "pet_id": "pet_12345678",
            "date": "2025-08-16",
            "events": [
                {
                    "event_id": "evt_12345678",
                    "timestamp": datetime.now(timezone.utc),
                    "behavior": "Sleep",
                    "confidence": 0.95,
                    "description": "Pet appears to be sleeping"
                }
            ],
            "summary": "Normal activity detected",
            "risk_flags": []
        }
        
        result = output_validator.validate_timeline_output(test_timeline)
        assert result.pet_id == "pet_12345678"
        assert len(result.events) == 1
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    return passed, failed

def test_security_scenarios():
    """Test security-specific scenarios"""
    print("\n" + "=" * 60)
    print("SECURITY VALIDATION TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # Test 1: SQL Injection Protection
    print("\n1. Testing SQL injection protection...", end=" ")
    try:
        from common.security.input_validators import InputValidator
        
        validator = InputValidator()
        malicious_data = {
            "collar_id": "'; DROP TABLE collars; --",
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }
        
        try:
            validator.validate_collar_data(malicious_data)
            print("❌ Should have rejected malicious input")
            failed += 1
        except ValueError:
            print("✓")
            passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 2: XSS Protection
    print("2. Testing XSS protection...", end=" ")
    try:
        from common.security.output_schemas import OutputValidator
        
        output_validator = OutputValidator()
        malicious_output = {
            "pet_id": "pet_12345678",
            "date": "2025-08-16",
            "events": [{
                "event_id": "evt_12345678",
                "timestamp": datetime.now(timezone.utc),
                "behavior": "Sleep",
                "confidence": 0.95,
                "description": "<script>alert('xss')</script>Pet sleeping"
            }],
            "summary": "javascript:alert('xss')Normal day",
            "risk_flags": []
        }
        
        result = output_validator.validate_timeline_output(malicious_output)
        assert '<script>' not in result.events[0].description
        assert 'javascript:' not in result.summary
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 3: Input Size Limits
    print("3. Testing input size limits...", end=" ")
    try:
        from common.security.input_validators import InputValidator
        
        validator = InputValidator()
        oversized_data = {
            "collar_id": "x" * 10000,  # Too long
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }
        
        try:
            validator.validate_collar_data(oversized_data)
            print("❌ Should have rejected oversized input")
            failed += 1
        except ValueError:
            print("✓")
            passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 4: Location Privacy
    print("4. Testing location privacy...", end=" ")
    try:
        from common.security.input_validators import InputValidator
        
        validator = InputValidator()
        precise_location = {
            "collar_id": "SN-12345",
            "timestamp": datetime.now(timezone.utc),
            "heart_rate": 80,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006123456789, 40.712834567891]  # High precision
            }
        }
        
        result = validator.validate_collar_data(precise_location)
        coords = result.location["coordinates"]
        
        # Check precision is limited
        coord_str = str(coords[0])
        if '.' in coord_str:
            decimal_places = len(coord_str.split('.')[1])
            assert decimal_places <= 6, f"Too much precision: {decimal_places} places"
        
        print("✓")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    return passed, failed

def test_performance_basics():
    """Test basic performance requirements"""
    print("\n" + "=" * 60)
    print("PERFORMANCE VALIDATION TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # Test 1: Response time for single analysis
    print("\n1. Testing analysis response time...", end=" ")
    try:
        from behavioral_interpreter.interpreter import BehavioralInterpreter
        
        interpreter = BehavioralInterpreter()
        test_data = [{
            "timestamp": "2025-08-16T12:00:00Z",
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]
        
        start_time = time.time()
        result = interpreter.analyze_timeline(test_data)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        assert analysis_time < 2.0, f"Too slow: {analysis_time:.2f}s"
        
        print(f"✓ ({analysis_time:.3f}s)")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    # Test 2: Rate limiter performance
    print("2. Testing rate limiter performance...", end=" ")
    try:
        from common.security.rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter(max_tokens=1000, refill_rate=100.0)
        
        start_time = time.time()
        for i in range(1000):
            rate_limiter.acquire(f"user_{i % 10}", 1)
        end_time = time.time()
        
        total_time = end_time - start_time
        requests_per_second = 1000 / total_time
        assert requests_per_second > 100, f"Too slow: {requests_per_second:.0f} req/s"
        
        print(f"✓ ({requests_per_second:.0f} req/s)")
        passed += 1
    except Exception as e:
        print(f"❌ {e}")
        failed += 1
    
    return passed, failed

def main():
    """Main test runner"""
    print("Petty Production System Validation")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    # Run test suites
    test_suites = [
        test_basic_functionality,
        test_security_scenarios,
        test_performance_basics
    ]
    
    for test_suite in test_suites:
        try:
            passed, failed = test_suite()
            total_passed += passed
            total_failed += failed
        except Exception as e:
            print(f"Test suite failed: {e}")
            total_failed += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests Passed: {total_passed}")
    print(f"Total Tests Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ Petty system is ready for production")
        return 0
    else:
        print(f"\n❌ {total_failed} validation test(s) failed")
        print("⚠️  System needs fixes before production")
        return 1

if __name__ == "__main__":
    sys.exit(main())
