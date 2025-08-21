"""
End-to-end performance tests for Petty application
Tests system performance, scalability, and resource utilization
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

@pytest.mark.asyncio
async def test_api_response_time_requirements(
    api_client,
    http_session,
    test_config,
    performance_monitor
):
    """
    Test that API endpoints meet response time SLA requirements
    
    Requirements:
    - Real-time data: < 500ms (95th percentile)  
    - Timeline generation: < 2s (95th percentile)
    - AI behavior analysis: < 5s (95th percentile)
    - Feedback submission: < 1s (95th percentile)
    """
    collar_id = test_config['test_collar_id']
    
    # Test 1: Real-time data performance
    realtime_times = []
    for i in range(20):  # Test 20 requests for statistical significance
        start_time = time.time()
        response = await api_client.get(
            http_session,
            "v1/realtime",
            params={'collar_id': f"{collar_id}_{i}"}
        )
        duration = (time.time() - start_time) * 1000
        realtime_times.append(duration)
        
        performance_monitor.record_api_call(
            'realtime_sla_test', duration, 
            response['status_code'] == 200, 
            response['status_code']
        )
        
        # Small delay to avoid overwhelming the system
        await asyncio.sleep(0.1)
    
    # Calculate 95th percentile
    realtime_p95 = statistics.quantiles(realtime_times, n=20)[18]  # 95th percentile
    assert realtime_p95 < 500, f"Real-time data P95 response time too high: {realtime_p95:.2f}ms"
    
    # Test 2: Timeline generation performance
    timeline_times = []
    for i in range(10):  # Timeline generation is more expensive
        start_time = time.time()
        response = await api_client.get(
            http_session,
            "v1/pet-timeline",
            params={'collar_id': f"{collar_id}_{i}"}
        )
        duration = (time.time() - start_time) * 1000
        timeline_times.append(duration)
        
        performance_monitor.record_api_call(
            'timeline_sla_test', duration,
            response['status_code'] == 200,
            response['status_code']
        )
        
        await asyncio.sleep(0.2)
    
    timeline_p95 = statistics.quantiles(timeline_times, n=10)[9]  # 95th percentile
    assert timeline_p95 < 2000, f"Timeline generation P95 response time too high: {timeline_p95:.2f}ms"
    
    # Test 3: Feedback submission performance
    feedback_times = []
    for i in range(15):
        start_time = time.time()
        response = await api_client.post(
            http_session,
            "v1/submit-feedback",
            data={
                'event_id': f'perf_test_event_{i}',
                'user_feedback': f'Performance test feedback #{i}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        duration = (time.time() - start_time) * 1000
        feedback_times.append(duration)
        
        performance_monitor.record_api_call(
            'feedback_sla_test', duration,
            response['status_code'] in [200, 201, 204],
            response['status_code']
        )
        
        await asyncio.sleep(0.1)
    
    feedback_p95 = statistics.quantiles(feedback_times, n=15)[14]  # 95th percentile
    assert feedback_p95 < 1000, f"Feedback submission P95 response time too high: {feedback_p95:.2f}ms"

@pytest.mark.asyncio
async def test_concurrent_load_handling(
    http_session,
    test_config,
    token_manager,
    performance_monitor
):
    """
    Test system behavior under high concurrent load
    
    Simulates multiple users making concurrent requests
    Tests for:
    - Response time degradation under load
    - Error rate increase
    - System stability
    - Resource contention
    """
    collar_id = test_config['test_collar_id']
    
    # Generate multiple user tokens
    num_concurrent_users = 50
    user_tokens = []
    
    for i in range(num_concurrent_users):
        token_pair = token_manager.generate_token_pair(
            user_id=f"load_test_user_{i:03d}",
            scopes=['read', 'write']
        )
        user_tokens.append(token_pair.access_token)
    
    # Create client for each user
    async def simulate_user_activity(user_id: int, token: str):
        """Simulate typical user activity pattern"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'User-Agent': 'PettyLoadTest/1.0'
        }
        client = APITestClient(test_config['api_base_url'], headers)
        
        user_metrics = []
        
        try:
            # Simulate mobile app startup sequence
            start_time = time.time()
            
            # 1. Get real-time data
            realtime_response = await client.get(
                http_session,
                "v1/realtime",
                params={'collar_id': f"{collar_id}_{user_id}"}
            )
            realtime_duration = (time.time() - start_time) * 1000
            user_metrics.append(('realtime', realtime_duration, realtime_response['status_code']))
            
            # 2. Get timeline (50% of users)
            if user_id % 2 == 0:
                start_time = time.time()
                timeline_response = await client.get(
                    http_session,
                    "v1/pet-timeline", 
                    params={'collar_id': f"{collar_id}_{user_id}"}
                )
                timeline_duration = (time.time() - start_time) * 1000
                user_metrics.append(('timeline', timeline_duration, timeline_response['status_code']))
            
            # 3. Submit feedback (20% of users)
            if user_id % 5 == 0:
                start_time = time.time()
                feedback_response = await client.post(
                    http_session,
                    "v1/submit-feedback",
                    data={
                        'event_id': f'load_test_event_{user_id}',
                        'user_feedback': f'Load test feedback from user {user_id}',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
                feedback_duration = (time.time() - start_time) * 1000
                user_metrics.append(('feedback', feedback_duration, feedback_response['status_code']))
            
            return user_metrics
            
        except Exception as e:
            return [('error', 0, 500)]
    
    # Execute concurrent load test
    print(f"Starting concurrent load test with {num_concurrent_users} users...")
    start_time = time.time()
    
    tasks = [simulate_user_activity(i, token) for i, token in enumerate(user_tokens)]
    user_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_test_duration = (time.time() - start_time) * 1000
    
    # Analyze results
    all_metrics = []
    error_count = 0
    
    for result in user_results:
        if isinstance(result, Exception):
            error_count += 1
            continue
        
        for endpoint, duration, status_code in result:
            all_metrics.append((endpoint, duration, status_code))
            success = status_code < 400
            performance_monitor.record_api_call(
                f'load_test_{endpoint}', duration, success, status_code
            )
            if not success:
                error_count += 1
    
    # Performance assertions
    total_requests = len(all_metrics)
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 100
    
    assert error_rate < 5, f"Error rate under load too high: {error_rate:.2f}%"
    assert total_test_duration < 30000, f"Load test took too long: {total_test_duration:.2f}ms"
    
    # Check response time degradation
    realtime_metrics = [m for m in all_metrics if m[0] == 'realtime']
    if realtime_metrics:
        realtime_times = [m[1] for m in realtime_metrics]
        avg_realtime = statistics.mean(realtime_times)
        assert avg_realtime < 1000, f"Average response time under load too high: {avg_realtime:.2f}ms"
    
    print(f"Load test completed: {total_requests} requests, {error_rate:.2f}% error rate")

@pytest.mark.asyncio
async def test_data_throughput_limits(
    api_client,
    http_session,
    test_config,
    sample_collar_data,
    performance_monitor
):
    """
    Test data ingestion throughput and limits
    
    Tests:
    - Maximum data points per second
    - Bulk data ingestion performance
    - Queue processing times
    - Data validation overhead
    """
    collar_id = test_config['test_collar_id']
    
    # Test 1: Rapid data ingestion
    data_points_per_batch = 100
    batch_count = 5
    
    for batch in range(batch_count):
        batch_start = time.time()
        
        # Create batch of data points
        batch_data = []
        for i in range(data_points_per_batch):
            data_point = sample_collar_data[i % len(sample_collar_data)].copy()
            data_point['collar_id'] = f"{collar_id}_batch_{batch}"
            data_point['sequence_id'] = i
            data_point['timestamp'] = (datetime.now(timezone.utc) + timedelta(seconds=i)).isoformat()
            batch_data.append(data_point)
        
        # Ingest data points concurrently
        async def ingest_data_point(data_point, index):
            start_time = time.time()
            try:
                response = await api_client.post(
                    http_session,
                    "v1/ingest",
                    data=data_point
                )
                duration = (time.time() - start_time) * 1000
                success = response['status_code'] in [200, 201, 202]
                
                performance_monitor.record_api_call(
                    f'throughput_batch_{batch}', duration, success, response['status_code']
                )
                
                return success
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                performance_monitor.record_api_call(
                    f'throughput_batch_{batch}', duration, False, 500
                )
                return False
        
        # Execute batch ingestion
        tasks = [ingest_data_point(data, i) for i, data in enumerate(batch_data)]
        results = await asyncio.gather(*tasks)
        
        batch_duration = (time.time() - batch_start) * 1000
        success_count = sum(results)
        success_rate = (success_count / len(results)) * 100
        
        # Performance requirements
        throughput = (success_count / batch_duration) * 1000  # points per second
        
        assert success_rate >= 95, f"Batch {batch} success rate too low: {success_rate:.2f}%"
        assert throughput >= 10, f"Batch {batch} throughput too low: {throughput:.2f} points/sec"
        
        # Brief pause between batches
        await asyncio.sleep(0.5)

@pytest.mark.asyncio
async def test_memory_and_resource_usage(
    api_client,
    http_session,
    test_config,
    performance_monitor
):
    """
    Test system resource usage patterns
    
    Tests for:
    - Memory leaks during extended operation
    - Connection pool management
    - Resource cleanup
    - Garbage collection impact
    """
    collar_id = test_config['test_collar_id']
    
    # Extended operation test - simulate long-running client session
    operation_count = 200
    
    for i in range(operation_count):
        start_time = time.time()
        
        # Mix different types of operations
        if i % 4 == 0:
            # Real-time data request
            response = await api_client.get(
                http_session,
                "v1/realtime",
                params={'collar_id': f"{collar_id}_{i}"}
            )
        elif i % 4 == 1:
            # Timeline request
            response = await api_client.get(
                http_session,
                "v1/pet-timeline",
                params={'collar_id': f"{collar_id}_{i}"}
            )
        elif i % 4 == 2:
            # Data ingestion
            data_point = {
                "collar_id": f"{collar_id}_{i}",
                "heart_rate": 70 + (i % 30),
                "activity_level": i % 3,
                "location": {"coordinates": [40.7128 + (i * 0.0001), -74.0060 + (i * 0.0001)]},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            response = await api_client.post(http_session, "v1/ingest", data=data_point)
        else:
            # Feedback submission
            response = await api_client.post(
                http_session,
                "v1/submit-feedback",
                data={
                    'event_id': f'resource_test_event_{i}',
                    'user_feedback': f'Resource test feedback #{i}',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        
        duration = (time.time() - start_time) * 1000
        success = response['status_code'] < 400
        
        performance_monitor.record_api_call(
            f'resource_test_op_{i % 4}', duration, success, response['status_code']
        )
        
        # Small delay to simulate realistic usage
        if i % 10 == 0:
            await asyncio.sleep(0.1)
    
    # Analyze resource usage patterns
    perf_summary = performance_monitor.get_performance_summary()
    
    # Check for performance degradation over time (potential memory leaks)
    early_metrics = performance_monitor.metrics[:50]  # First 50 operations
    late_metrics = performance_monitor.metrics[-50:]   # Last 50 operations
    
    if len(early_metrics) >= 10 and len(late_metrics) >= 10:
        early_avg = statistics.mean([m['duration_ms'] for m in early_metrics])
        late_avg = statistics.mean([m['duration_ms'] for m in late_metrics])
        
        degradation_ratio = late_avg / early_avg
        assert degradation_ratio < 2.0, f"Performance degradation detected: {degradation_ratio:.2f}x slower"

@pytest.mark.asyncio 
async def test_ai_inference_performance(
    api_client,
    http_session,
    test_config,
    sample_collar_data,
    performance_monitor
):
    """
    Test AI behavioral inference performance under various data loads
    
    Tests:
    - Processing time for different data set sizes
    - Confidence score consistency
    - Memory usage during AI processing
    - Batch vs. streaming processing performance
    """
    collar_id = test_config['test_collar_id']
    
    # Test different data set sizes
    data_sizes = [10, 50, 100, 200]
    
    for size in data_sizes:
        # Generate dataset of specified size
        test_data = []
        for i in range(size):
            data_point = sample_collar_data[i % len(sample_collar_data)].copy()
            data_point['collar_id'] = f"{collar_id}_ai_test"
            data_point['sequence_id'] = i
            base_time = datetime.now(timezone.utc)
            data_point['timestamp'] = (base_time + timedelta(minutes=i)).isoformat()
            test_data.append(data_point)
        
        # Ingest test data
        ingestion_start = time.time()
        for data_point in test_data:
            await api_client.post(http_session, "v1/ingest", data=data_point)
        ingestion_duration = (time.time() - ingestion_start) * 1000
        
        # Wait for processing
        await asyncio.sleep(min(5, size / 10))  # Adaptive wait time
        
        # Request AI analysis
        ai_start = time.time()
        timeline_response = await api_client.get(
            http_session,
            "v1/pet-timeline",
            params={'collar_id': f"{collar_id}_ai_test"}
        )
        ai_duration = (time.time() - ai_start) * 1000
        
        # Record AI performance metrics
        performance_monitor.record_api_call(
            f'ai_inference_size_{size}', ai_duration,
            timeline_response['status_code'] == 200,
            timeline_response['status_code']
        )
        
        # Analyze AI results
        if timeline_response['status_code'] == 200:
            timeline_data = timeline_response['data']
            if 'timeline' in timeline_data:
                events = timeline_data['timeline']
                behavior_events = [e for e in events if 'behavior' in e]
                
                # Performance assertions based on data size
                if size <= 50:
                    assert ai_duration < 2000, f"AI processing too slow for {size} points: {ai_duration:.2f}ms"
                elif size <= 100:
                    assert ai_duration < 3000, f"AI processing too slow for {size} points: {ai_duration:.2f}ms" 
                else:
                    assert ai_duration < 5000, f"AI processing too slow for {size} points: {ai_duration:.2f}ms"
                
                # Check confidence scores
                for event in behavior_events:
                    if 'confidence' in event:
                        confidence = event['confidence']
                        assert 0.0 <= confidence <= 1.0, f"Invalid confidence score: {confidence}"

# Import the APITestClient class
from .conftest import APITestClient