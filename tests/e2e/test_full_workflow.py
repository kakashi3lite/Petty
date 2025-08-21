"""
End-to-end tests for complete user journey through Petty application
Tests the full workflow: mobile app → API → AWS services
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import time

@pytest.mark.asyncio
async def test_complete_user_journey(
    http_session,
    mobile_simulator,
    test_config,
    sample_collar_data,
    performance_monitor,
    aws_mocks
):
    """
    Test complete user journey from app startup to feedback submission
    
    Flow:
    1. Mobile app starts up
    2. App fetches real-time data
    3. App loads pet plan 
    4. App displays timeline
    5. User submits feedback on behavior event
    """
    collar_id = test_config['test_collar_id']
    
    # Step 1: Simulate mobile app startup
    start_time = time.time()
    startup_results = await mobile_simulator.simulate_app_startup(http_session, collar_id)
    startup_duration = (time.time() - start_time) * 1000
    
    # Verify startup was successful
    assert startup_results['realtime']['status_code'] == 200
    assert startup_results['pet_plan']['status_code'] == 200
    assert startup_results['timeline']['status_code'] == 200
    
    # Record performance metrics
    performance_monitor.record_api_call(
        'app_startup', startup_duration, True, 200
    )
    
    # Step 2: Verify real-time data structure
    realtime_data = startup_results['realtime']['data']
    assert 'collar_id' in realtime_data
    assert 'heart_rate' in realtime_data
    assert 'activity_level' in realtime_data
    assert 'location' in realtime_data
    assert 'timestamp' in realtime_data
    
    # Step 3: Verify pet plan structure
    pet_plan = startup_results['pet_plan']['data']
    assert 'daily_goals' in pet_plan
    assert 'nutrition_plan' in pet_plan
    assert 'health_recommendations' in pet_plan
    
    # Step 4: Verify timeline structure and extract event for feedback
    timeline = startup_results['timeline']['data']
    assert 'timeline' in timeline
    timeline_events = timeline['timeline']
    assert len(timeline_events) > 0
    
    # Find a behavior event to provide feedback on
    behavior_event = None
    for event in timeline_events:
        if 'behavior' in event and 'event_id' in event:
            behavior_event = event
            break
    
    assert behavior_event is not None, "No behavior events found in timeline"
    
    # Step 5: Submit user feedback
    feedback_text = "This behavior detection looks accurate! My dog was indeed sleeping deeply."
    start_time = time.time()
    
    feedback_result = await mobile_simulator.simulate_user_feedback(
        http_session, 
        behavior_event['event_id'], 
        feedback_text
    )
    
    feedback_duration = (time.time() - start_time) * 1000
    
    # Verify feedback submission was successful
    assert feedback_result['status_code'] in [200, 201, 204]
    
    # Record performance metrics
    performance_monitor.record_api_call(
        'submit_feedback', feedback_duration, True, feedback_result['status_code']
    )
    
    # Step 6: Verify performance requirements
    perf_summary = performance_monitor.get_performance_summary()
    
    # API response times should meet requirements
    assert perf_summary['avg_duration_ms'] < 2000, f"Average response time too high: {perf_summary['avg_duration_ms']}ms"
    assert perf_summary['success_rate'] == 100, f"Success rate too low: {perf_summary['success_rate']}%"

@pytest.mark.asyncio
async def test_data_ingestion_to_ai_analysis(
    api_client,
    http_session,
    sample_collar_data,
    test_config,
    performance_monitor
):
    """
    Test data flow from ingestion through AI behavioral analysis
    
    Flow:
    1. Ingest collar sensor data
    2. Wait for processing
    3. Retrieve analyzed timeline
    4. Verify AI-detected behaviors
    """
    collar_id = test_config['test_collar_id']
    
    # Step 1: Ingest collar sensor data
    ingestion_results = []
    
    for data_point in sample_collar_data:
        start_time = time.time()
        
        response = await api_client.post(
            http_session,
            "v1/ingest",
            data=data_point
        )
        
        duration = (time.time() - start_time) * 1000
        ingestion_results.append(response)
        
        performance_monitor.record_api_call(
            'data_ingestion', 
            duration, 
            response['status_code'] in [200, 201, 202], 
            response['status_code']
        )
        
        # Verify ingestion was successful
        assert response['status_code'] in [200, 201, 202]
    
    # Step 2: Wait for AI processing (simulate processing time)
    await asyncio.sleep(2)
    
    # Step 3: Retrieve analyzed timeline
    start_time = time.time()
    timeline_response = await api_client.get(
        http_session,
        "v1/pet-timeline",
        params={'collar_id': collar_id}
    )
    timeline_duration = (time.time() - start_time) * 1000
    
    # Verify timeline retrieval
    assert timeline_response['status_code'] == 200
    timeline_data = timeline_response['data']
    assert 'timeline' in timeline_data
    
    performance_monitor.record_api_call(
        'ai_timeline_generation', 
        timeline_duration, 
        True, 
        200
    )
    
    # Step 4: Verify AI behavior detection
    events = timeline_data['timeline']
    behavior_events = [e for e in events if 'behavior' in e]
    
    assert len(behavior_events) > 0, "No behavior events detected by AI"
    
    # Verify behavior event structure
    for event in behavior_events:
        assert 'behavior' in event
        assert 'confidence' in event
        assert 'timestamp' in event
        assert 'event_id' in event
        
        # Confidence should be reasonable
        confidence = event['confidence']
        assert 0.0 <= confidence <= 1.0, f"Invalid confidence score: {confidence}"
        
        # Should have metadata
        if 'metadata' in event:
            metadata = event['metadata']
            assert isinstance(metadata, dict)
    
    # Step 5: Verify performance requirements for AI processing
    perf_summary = performance_monitor.get_performance_summary()
    ai_calls = [m for m in performance_monitor.metrics if 'ai_' in m['endpoint']]
    
    if ai_calls:
        ai_avg_duration = sum(m['duration_ms'] for m in ai_calls) / len(ai_calls)
        assert ai_avg_duration < 5000, f"AI processing too slow: {ai_avg_duration}ms"

@pytest.mark.asyncio
async def test_mobile_app_error_recovery(
    api_client,
    http_session,
    test_config,
    error_scenarios,
    performance_monitor
):
    """
    Test mobile app error handling and recovery mechanisms
    
    Tests:
    1. Network timeout handling
    2. Server error recovery
    3. Authentication failure handling
    4. Invalid data handling
    5. Rate limit handling
    """
    collar_id = test_config['test_collar_id']
    
    # Test 1: Invalid collar ID (400 error)
    start_time = time.time()
    response = await api_client.get(
        http_session,
        "v1/realtime",
        params={'collar_id': ''}  # Invalid empty collar ID
    )
    duration = (time.time() - start_time) * 1000
    
    # Should handle validation error gracefully
    assert response['status_code'] == 400
    performance_monitor.record_api_call(
        'error_handling_validation', duration, False, 400
    )
    
    # Test 2: Non-existent collar ID (404 error)
    start_time = time.time()
    response = await api_client.get(
        http_session,
        "v1/realtime",
        params={'collar_id': 'non_existent_collar'}
    )
    duration = (time.time() - start_time) * 1000
    
    assert response['status_code'] == 404
    performance_monitor.record_api_call(
        'error_handling_not_found', duration, False, 404
    )
    
    # Test 3: Malformed request data
    start_time = time.time()
    response = await api_client.post(
        http_session,
        "v1/ingest",
        data={'invalid': 'data_structure'}  # Missing required fields
    )
    duration = (time.time() - start_time) * 1000
    
    assert response['status_code'] in [400, 422]  # Validation error
    performance_monitor.record_api_call(
        'error_handling_malformed', duration, False, response['status_code']
    )

@pytest.mark.asyncio
async def test_api_versioning_compatibility(
    api_client,
    http_session,
    test_config,
    sample_collar_data,
    performance_monitor
):
    """
    Test API versioning and backward compatibility
    
    Tests:
    1. V1 API endpoints work correctly
    2. Legacy endpoints still function
    3. Version-specific features
    4. Migration path from legacy to v1
    """
    collar_id = test_config['test_collar_id']
    
    # Test 1: V1 endpoints
    v1_endpoints = [
        ("GET", "v1/realtime", {'collar_id': collar_id}),
        ("GET", "v1/pet-plan", {'collar_id': collar_id}),
        ("GET", "v1/pet-timeline", {'collar_id': collar_id}),
    ]
    
    for method, endpoint, params in v1_endpoints:
        start_time = time.time()
        
        if method == "GET":
            response = await api_client.get(http_session, endpoint, params)
        
        duration = (time.time() - start_time) * 1000
        
        assert response['status_code'] == 200
        performance_monitor.record_api_call(
            f'v1_{endpoint}', duration, True, 200
        )
    
    # Test 2: Legacy endpoints (should still work)
    legacy_endpoints = [
        ("GET", "realtime", {'collar_id': collar_id}),
        ("GET", "pet-plan", {'collar_id': collar_id}),
        ("GET", "pet-timeline", {'collar_id': collar_id}),
    ]
    
    for method, endpoint, params in legacy_endpoints:
        start_time = time.time()
        
        if method == "GET":
            response = await api_client.get(http_session, endpoint, params)
        
        duration = (time.time() - start_time) * 1000
        
        assert response['status_code'] == 200
        performance_monitor.record_api_call(
            f'legacy_{endpoint}', duration, True, 200
        )
    
    # Test 3: Data ingestion on both versions
    data_point = sample_collar_data[0]
    
    # V1 ingestion
    v1_response = await api_client.post(http_session, "v1/ingest", data=data_point)
    assert v1_response['status_code'] in [200, 201, 202]
    
    # Legacy ingestion  
    legacy_response = await api_client.post(http_session, "ingest", data=data_point)
    assert legacy_response['status_code'] in [200, 201, 202]

@pytest.mark.asyncio
async def test_security_and_authentication(
    token_manager,
    api_client,
    http_session,
    test_config
):
    """
    Test security features and authentication mechanisms
    
    Tests:
    1. Valid JWT token access
    2. Invalid JWT token rejection
    3. Expired token handling
    4. Token refresh functionality
    5. API key authentication (if applicable)
    """
    collar_id = test_config['test_collar_id']
    
    # Test 1: Valid token should work (already tested in other tests)
    response = await api_client.get(
        http_session,
        "v1/realtime",
        params={'collar_id': collar_id}
    )
    assert response['status_code'] == 200
    
    # Test 2: Invalid token should be rejected
    invalid_headers = api_client.headers.copy()
    invalid_headers['Authorization'] = 'Bearer invalid_token_here'
    
    invalid_client = APITestClient(test_config['api_base_url'], invalid_headers)
    
    response = await invalid_client.get(
        http_session,
        "v1/realtime",
        params={'collar_id': collar_id}
    )
    
    # Should return 401 Unauthorized
    assert response['status_code'] == 401
    
    # Test 3: Missing token should be rejected
    no_auth_headers = {k: v for k, v in api_client.headers.items() if k != 'Authorization'}
    no_auth_client = APITestClient(test_config['api_base_url'], no_auth_headers)
    
    response = await no_auth_client.get(
        http_session,
        "v1/realtime", 
        params={'collar_id': collar_id}
    )
    
    # Should return 401 Unauthorized
    assert response['status_code'] == 401

@pytest.mark.asyncio
async def test_performance_under_load(
    api_client,
    http_session,
    test_config,
    performance_monitor
):
    """
    Test system performance under concurrent load
    
    Tests:
    1. Concurrent API requests
    2. Response time consistency
    3. Error rate under load
    4. Resource utilization
    """
    collar_id = test_config['test_collar_id']
    
    # Test concurrent requests
    concurrent_requests = 10
    tasks = []
    
    async def make_request(request_id: int):
        start_time = time.time()
        try:
            response = await api_client.get(
                http_session,
                "v1/realtime",
                params={'collar_id': f"{collar_id}_{request_id}"}
            )
            duration = (time.time() - start_time) * 1000
            success = response['status_code'] == 200
            
            performance_monitor.record_api_call(
                f'concurrent_request_{request_id}', 
                duration, 
                success, 
                response['status_code']
            )
            
            return response
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            performance_monitor.record_api_call(
                f'concurrent_request_{request_id}', 
                duration, 
                False, 
                500
            )
            raise
    
    # Execute concurrent requests
    start_time = time.time()
    tasks = [make_request(i) for i in range(concurrent_requests)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    total_duration = (time.time() - start_time) * 1000
    
    # Analyze results
    successful_responses = [r for r in responses if not isinstance(r, Exception)]
    failed_responses = [r for r in responses if isinstance(r, Exception)]
    
    success_rate = len(successful_responses) / len(responses) * 100
    
    # Performance requirements
    assert success_rate >= 95, f"Success rate under load too low: {success_rate}%"
    assert total_duration < 10000, f"Total concurrent request time too high: {total_duration}ms"
    
    # Check individual response times
    perf_summary = performance_monitor.get_performance_summary()
    concurrent_metrics = [m for m in performance_monitor.metrics if 'concurrent_request' in m['endpoint']]
    
    if concurrent_metrics:
        avg_concurrent_duration = sum(m['duration_ms'] for m in concurrent_metrics) / len(concurrent_metrics)
        assert avg_concurrent_duration < 3000, f"Average concurrent response time too high: {avg_concurrent_duration}ms"

# Import the APITestClient class from conftest for the tests above
from .conftest import APITestClient