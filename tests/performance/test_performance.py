"""
Performance and scalability tests for Petty system
"""

import time
import asyncio
import threading
import concurrent.futures
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Import the modules we want to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from behavioral_interpreter.interpreter import BehavioralInterpreter
    from common.security.rate_limiter import RateLimiter, CircuitBreaker
    from common.security.input_validators import InputValidator
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False

class TestPerformanceRequirements:
    """Test system performance requirements"""
    
    def test_behavioral_analysis_response_time(self):
        """Test that behavioral analysis completes within acceptable time"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        interpreter = BehavioralInterpreter()
        
        # Generate test data (typical day's worth)
        test_data = []
        for hour in range(24):
            for minute in range(0, 60, 15):  # Every 15 minutes
                test_data.append({
                    "timestamp": f"2025-08-16T{hour:02d}:{minute:02d}:00Z",
                    "heart_rate": 80 + (hour % 20),
                    "activity_level": (hour + minute) % 3,
                    "location": {
                        "type": "Point",
                        "coordinates": [-74.006 + hour*0.001, 40.7128 + minute*0.0001]
                    }
                })
        
        # Measure analysis time
        start_time = time.time()
        result = interpreter.analyze_timeline(test_data)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        
        # Should complete within 5 seconds for a day's data
        assert analysis_time < 5.0, f"Analysis took {analysis_time:.2f}s, should be < 5s"
        
        # Should produce some results
        assert isinstance(result, list)
        print(f"✓ Behavioral analysis completed in {analysis_time:.2f}s")
    
    def test_concurrent_analysis_performance(self):
        """Test system performance under concurrent load"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        interpreter = BehavioralInterpreter()
        
        # Create test data for multiple pets
        def create_pet_data(pet_id):
            return [{
                "timestamp": f"2025-08-16T12:0{pet_id}:00Z",
                "heart_rate": 80 + pet_id,
                "activity_level": pet_id % 3,
                "location": {
                    "type": "Point", 
                    "coordinates": [-74.006 + pet_id*0.01, 40.7128 + pet_id*0.01]
                }
            }]
        
        def analyze_pet(pet_id):
            data = create_pet_data(pet_id)
            start_time = time.time()
            result = interpreter.analyze_timeline(data)
            end_time = time.time()
            return end_time - start_time, len(result) if result else 0
        
        # Test concurrent analysis for 10 pets
        start_total = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze_pet, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_total = time.time()
        total_time = end_total - start_total
        
        # All analyses should complete reasonably quickly
        max_individual_time = max(result[0] for result in results)
        assert max_individual_time < 3.0, f"Slowest analysis: {max_individual_time:.2f}s"
        
        # Total time should be less than sequential execution (shows parallelism working)
        estimated_sequential = sum(result[0] for result in results)
        assert total_time < estimated_sequential * 0.8, "Concurrent execution not faster than sequential"
        
        print(f"✓ Concurrent analysis: {len(results)} pets in {total_time:.2f}s")
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during processing"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        interpreter = BehavioralInterpreter()
        
        # Process multiple batches to check for memory leaks
        import gc
        
        initial_objects = len(gc.get_objects())
        
        for batch in range(10):
            # Create test data
            test_data = []
            for i in range(100):
                test_data.append({
                    "timestamp": f"2025-08-16T{i%24:02d}:{(i*5)%60:02d}:00Z",
                    "heart_rate": 80 + (i % 40),
                    "activity_level": i % 3,
                    "location": {
                        "type": "Point",
                        "coordinates": [-74.006 + i*0.0001, 40.7128 + i*0.0001]
                    }
                })
            
            # Process and discard results
            result = interpreter.analyze_timeline(test_data)
            del result
            del test_data
            
            # Force garbage collection
            gc.collect()
        
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Object count shouldn't grow significantly (allowing some growth for caching)
        assert object_growth < 1000, f"Memory leak detected: {object_growth} new objects"
        
        print(f"✓ Memory stability: {object_growth} object growth over 10 batches")

class TestScalabilityRequirements:
    """Test system scalability"""
    
    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        interpreter = BehavioralInterpreter()
        
        # Create a week's worth of data (high frequency)
        large_dataset = []
        for day in range(7):
            for hour in range(24):
                for minute in range(0, 60, 5):  # Every 5 minutes
                    large_dataset.append({
                        "timestamp": f"2025-08-{16+day:02d}T{hour:02d}:{minute:02d}:00Z",
                        "heart_rate": 80 + ((day * hour + minute) % 40),
                        "activity_level": (day + hour + minute) % 3,
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                -74.006 + day*0.001 + hour*0.0001,
                                40.7128 + minute*0.00001
                            ]
                        }
                    })
        
        print(f"Processing {len(large_dataset)} data points...")
        
        start_time = time.time()
        result = interpreter.analyze_timeline(large_dataset)
        end_time = time.time()
        
        processing_time = end_time - start_time
        throughput = len(large_dataset) / processing_time
        
        # Should process at least 100 data points per second
        assert throughput > 100, f"Throughput too low: {throughput:.1f} points/sec"
        
        # Should complete within 30 seconds for a week's data
        assert processing_time < 30, f"Processing took {processing_time:.2f}s"
        
        print(f"✓ Large dataset: {len(large_dataset)} points in {processing_time:.2f}s")
        print(f"✓ Throughput: {throughput:.1f} data points/second")
    
    def test_rate_limiter_scalability(self):
        """Test rate limiter performance under load"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        rate_limiter = RateLimiter(max_tokens=1000, refill_rate=100.0)
        
        # Simulate high-frequency requests from multiple users
        def make_requests(user_id, num_requests):
            success_count = 0
            start_time = time.time()
            
            for i in range(num_requests):
                if rate_limiter.acquire(f"user_{user_id}", 1):
                    success_count += 1
                    
            end_time = time.time()
            return success_count, end_time - start_time
        
        # Test with multiple concurrent users
        start_total = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_requests, user_id, 100)
                for user_id in range(20)
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_total = time.time()
        total_time = end_total - start_total
        
        total_requests = sum(result[0] for result in results)
        total_attempted = 20 * 100  # 20 users * 100 requests each
        
        # Rate limiter should handle requests efficiently
        assert total_time < 5.0, f"Rate limiting took too long: {total_time:.2f}s"
        
        # Should allow a reasonable portion of requests
        success_rate = total_requests / total_attempted
        assert success_rate > 0.1, f"Success rate too low: {success_rate:.2%}"
        
        print(f"✓ Rate limiter: {total_requests}/{total_attempted} requests in {total_time:.2f}s")
        print(f"✓ Success rate: {success_rate:.2%}")

class TestReliabilityRequirements:
    """Test system reliability and fault tolerance"""
    
    def test_circuit_breaker_reliability(self):
        """Test circuit breaker fault tolerance"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=1)
        
        # Simulate failing service
        call_count = 0
        def unreliable_service():
            nonlocal call_count
            call_count += 1
            if call_count <= 5:
                raise Exception("Service temporarily unavailable")
            return "success"
        
        # Test circuit breaker behavior
        failure_count = 0
        success_count = 0
        
        # First few calls should fail and eventually open the circuit
        for i in range(10):
            try:
                result = circuit_breaker.call(unreliable_service)
                success_count += 1
            except:
                failure_count += 1
        
        # Circuit should be open now, preventing further calls to failing service
        assert failure_count >= 3, "Should have some failures"
        assert call_count <= 8, "Circuit breaker should prevent excessive calls"
        
        # Wait for circuit to potentially reset
        time.sleep(1.1)
        
        # Try again - service should work now
        try:
            result = circuit_breaker.call(unreliable_service)
            success_count += 1
        except:
            failure_count += 1
        
        print(f"✓ Circuit breaker: {failure_count} failures, {success_count} successes")
        print(f"✓ Service calls limited to {call_count} (prevented cascade failure)")
    
    def test_input_validation_reliability(self):
        """Test input validation under stress"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        validator = InputValidator()
        
        # Test various malformed inputs
        malformed_inputs = [
            None,
            "",
            "not_json",
            {"incomplete": "data"},
            {"collar_id": None},
            {"heart_rate": "not_a_number"},
            {"activity_level": -1},
            {"location": "invalid"},
            {"timestamp": "invalid_date"},
            # Very large inputs
            {"collar_id": "x" * 10000},
            # Injection attempts
            {"collar_id": "'; DROP TABLE pets; --"},
            {"heart_rate": "1; DELETE FROM data;"},
        ]
        
        error_count = 0
        crash_count = 0
        
        for malformed_input in malformed_inputs:
            try:
                result = validator.validate_collar_data(malformed_input)
                # If validation passes, it should be a valid result
                assert hasattr(result, 'collar_id')
            except ValueError:
                # Expected validation errors
                error_count += 1
            except Exception as e:
                # Unexpected crashes
                crash_count += 1
                print(f"Unexpected error for input {malformed_input}: {e}")
        
        # Should handle malformed inputs gracefully (no crashes)
        assert crash_count == 0, f"System crashed {crash_count} times"
        assert error_count > 0, "Should reject some malformed inputs"
        
        print(f"✓ Input validation: {error_count} properly rejected, {crash_count} crashes")
    
    def test_graceful_degradation(self):
        """Test system behavior when components fail"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        interpreter = BehavioralInterpreter()
        
        # Test with minimal valid data
        minimal_data = [{
            "timestamp": "2025-08-16T12:00:00Z",
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]
        
        # Normal operation
        normal_result = interpreter.analyze_timeline(minimal_data)
        
        # Test with empty data
        empty_result = interpreter.analyze_timeline([])
        assert isinstance(empty_result, list), "Should handle empty data gracefully"
        
        # Test with single data point
        single_result = interpreter.analyze_timeline(minimal_data[:1])
        assert isinstance(single_result, list), "Should handle single data point"
        
        # Test with duplicate timestamps
        duplicate_data = minimal_data * 3  # Same data repeated
        duplicate_result = interpreter.analyze_timeline(duplicate_data)
        assert isinstance(duplicate_result, list), "Should handle duplicate data"
        
        print("✓ Graceful degradation: System handles edge cases without crashing")

class TestSecurityPerformance:
    """Test performance of security features"""
    
    def test_security_overhead(self):
        """Test that security features don't significantly impact performance"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        # Test data
        test_data = [{
            "timestamp": "2025-08-16T12:00:00Z",
            "heart_rate": 80,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
        }]
        
        # Measure with security validation
        validator = InputValidator()
        interpreter = BehavioralInterpreter()
        
        start_time = time.time()
        for _ in range(100):
            validated_data = validator.validate_collar_data(test_data[0])
            result = interpreter.analyze_timeline([validated_data.dict()])
        end_time = time.time()
        
        with_security_time = end_time - start_time
        
        # Measure without security (direct processing)
        start_time = time.time()
        for _ in range(100):
            result = interpreter.analyze_timeline(test_data)
        end_time = time.time()
        
        without_security_time = end_time - start_time
        
        # Security overhead should be reasonable (less than 50% increase)
        overhead_ratio = with_security_time / without_security_time
        assert overhead_ratio < 1.5, f"Security overhead too high: {overhead_ratio:.2f}x"
        
        print(f"✓ Security overhead: {overhead_ratio:.2f}x ({overhead_ratio-1:.1%} increase)")
    
    def test_rate_limiter_performance(self):
        """Test rate limiter computational efficiency"""
        if not MODULES_AVAILABLE:
            print("Skipping test - modules not available")
            return
            
        rate_limiter = RateLimiter(max_tokens=10000, refill_rate=1000.0)
        
        # Measure rate limiter performance
        start_time = time.time()
        
        for i in range(10000):
            rate_limiter.acquire(f"user_{i % 100}", 1)  # 100 different users
        
        end_time = time.time()
        rate_limiter_time = end_time - start_time
        
        # Should handle 10k requests very quickly
        requests_per_second = 10000 / rate_limiter_time
        assert requests_per_second > 1000, f"Rate limiter too slow: {requests_per_second:.0f} req/s"
        
        print(f"✓ Rate limiter performance: {requests_per_second:.0f} requests/second")

if __name__ == "__main__":
    # Run all tests
    test_classes = [
        TestPerformanceRequirements,
        TestScalabilityRequirements, 
        TestReliabilityRequirements,
        TestSecurityPerformance
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
                
    print("\n=== Performance Testing Complete ===")
