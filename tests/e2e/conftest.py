"""
End-to-end test configuration and fixtures for Petty application
"""

import os
import json
import asyncio
import pytest
import boto3
from moto import mock_secretsmanager, mock_timestream_write, mock_timestream_query, mock_s3
from datetime import datetime, timezone
from typing import Dict, Any, List, AsyncGenerator
import aiohttp
from src.common.security.auth import ProductionTokenManager
from src.common.security.secrets_manager import ProductionSecretsManager
from src.common.observability.powertools import obs_manager

# Test configuration
TEST_CONFIG = {
    "api_base_url": os.getenv("TEST_API_URL", "http://localhost:3000"),
    "test_collar_id": "test_collar_001",
    "test_user_id": "test_user_001",
    "aws_region": "us-east-1",
    "timestream_db": "PettyDB-test",
    "timestream_table": "CollarMetrics",
    "s3_bucket": "petty-feedback-data-test"
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return TEST_CONFIG

@pytest.fixture(scope="session")
@mock_secretsmanager
@mock_timestream_write
@mock_timestream_query
@mock_s3
def aws_mocks():
    """Set up AWS service mocks for testing"""
    # Set up Secrets Manager mock
    secrets_client = boto3.client('secretsmanager', region_name=TEST_CONFIG['aws_region'])
    
    # Create JWT keys secret
    secrets_client.create_secret(
        Name='petty/jwt-keys-test',
        Description='Test JWT keys',
        SecretString=json.dumps({
            'private_key': 'test_private_key',
            'public_key': 'test_public_key',
            'algorithm': 'RS256'
        })
    )
    
    # Create database credentials secret
    secrets_client.create_secret(
        Name='petty/db-petty-test',
        Description='Test database credentials',
        SecretString=json.dumps({
            'username': 'test_user',
            'password': 'test_password',
            'host': 'localhost',
            'port': '5432',
            'database': 'petty_test'
        })
    )
    
    # Create encryption keys secret
    secrets_client.create_secret(
        Name='petty/encryption-keys/pii-test',
        Description='Test PII encryption key',
        SecretString=json.dumps({
            'key': 'test_encryption_key_32_chars_long!',
            'purpose': 'pii_encryption'
        })
    )
    
    # Set up Timestream mock
    timestream_write_client = boto3.client('timestream-write', region_name=TEST_CONFIG['aws_region'])
    timestream_query_client = boto3.client('timestream-query', region_name=TEST_CONFIG['aws_region'])
    
    # Set up S3 mock
    s3_client = boto3.client('s3', region_name=TEST_CONFIG['aws_region'])
    s3_client.create_bucket(Bucket=TEST_CONFIG['s3_bucket'])
    
    yield {
        'secrets': secrets_client,
        'timestream_write': timestream_write_client,
        'timestream_query': timestream_query_client,
        's3': s3_client
    }

@pytest.fixture
def token_manager():
    """Production token manager fixture"""
    return ProductionTokenManager()

@pytest.fixture
def secrets_manager():
    """Production secrets manager fixture"""
    return ProductionSecretsManager(region_name=TEST_CONFIG['aws_region'])

@pytest.fixture
def valid_access_token(token_manager):
    """Generate a valid access token for testing"""
    token_pair = token_manager.generate_token_pair(
        user_id=TEST_CONFIG['test_user_id'],
        scopes=['read', 'write']
    )
    return token_pair.access_token

@pytest.fixture
def sample_collar_data():
    """Generate sample collar sensor data"""
    base_time = datetime.now(timezone.utc)
    
    return [
        {
            "timestamp": base_time.isoformat(),
            "collar_id": TEST_CONFIG['test_collar_id'],
            "heart_rate": 65,
            "activity_level": 0,
            "location": {
                "coordinates": [40.7128, -74.0060],
                "accuracy": 5.0
            },
            "temperature": 38.5,
            "battery_level": 85
        },
        {
            "timestamp": base_time.replace(minute=base_time.minute + 1).isoformat(),
            "collar_id": TEST_CONFIG['test_collar_id'],
            "heart_rate": 120,
            "activity_level": 2,
            "location": {
                "coordinates": [40.7130, -74.0062],
                "accuracy": 8.0
            },
            "temperature": 39.2,
            "battery_level": 84
        },
        {
            "timestamp": base_time.replace(minute=base_time.minute + 2).isoformat(),
            "collar_id": TEST_CONFIG['test_collar_id'],
            "heart_rate": 45,
            "activity_level": 0,
            "location": {
                "coordinates": [40.7128, -74.0060],
                "accuracy": 4.0
            },
            "temperature": 38.3,
            "battery_level": 83
        }
    ]

@pytest.fixture
async def http_session():
    """Async HTTP session for API testing"""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
def api_headers(valid_access_token):
    """Standard API headers with authentication"""
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {valid_access_token}',
        'User-Agent': 'PettyE2ETest/1.0',
        'X-Correlation-ID': 'e2e-test-correlation-id'
    }

class APITestClient:
    """Test client for API interactions"""
    
    def __init__(self, base_url: str, headers: Dict[str, str]):
        self.base_url = base_url
        self.headers = headers
    
    async def post(self, session: aiohttp.ClientSession, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to API"""
        url = f"{self.base_url}/{endpoint}"
        async with session.post(url, json=data, headers=self.headers) as response:
            response_data = await response.json()
            return {
                'status_code': response.status,
                'data': response_data,
                'headers': dict(response.headers)
            }
    
    async def get(self, session: aiohttp.ClientSession, endpoint: str, params: Dict[str, str] = None) -> Dict[str, Any]:
        """Make GET request to API"""
        url = f"{self.base_url}/{endpoint}"
        async with session.get(url, params=params, headers=self.headers) as response:
            response_data = await response.json()
            return {
                'status_code': response.status,
                'data': response_data,
                'headers': dict(response.headers)
            }

@pytest.fixture
def api_client(test_config, api_headers):
    """API test client fixture"""
    return APITestClient(test_config['api_base_url'], api_headers)

# Performance test utilities
class PerformanceMonitor:
    """Monitor performance metrics during E2E tests"""
    
    def __init__(self):
        self.metrics = []
    
    def record_api_call(self, endpoint: str, duration_ms: float, success: bool, status_code: int):
        """Record API call metrics"""
        self.metrics.append({
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'success': success,
            'status_code': status_code,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance test summary"""
        if not self.metrics:
            return {'total_calls': 0}
        
        successful_calls = [m for m in self.metrics if m['success']]
        failed_calls = [m for m in self.metrics if not m['success']]
        
        durations = [m['duration_ms'] for m in self.metrics]
        
        return {
            'total_calls': len(self.metrics),
            'successful_calls': len(successful_calls),
            'failed_calls': len(failed_calls),
            'success_rate': len(successful_calls) / len(self.metrics) * 100,
            'avg_duration_ms': sum(durations) / len(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'p95_duration_ms': sorted(durations)[int(len(durations) * 0.95)],
            'error_rates': {}
        }

@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture"""
    return PerformanceMonitor()

# Mobile app simulation utilities
class MobileAppSimulator:
    """Simulate mobile app behavior for E2E testing"""
    
    def __init__(self, api_client: APITestClient):
        self.api_client = api_client
    
    async def simulate_app_startup(self, session: aiohttp.ClientSession, collar_id: str) -> Dict[str, Any]:
        """Simulate mobile app startup sequence"""
        results = {}
        
        # 1. Get real-time data
        realtime_response = await self.api_client.get(
            session, 
            "v1/realtime", 
            params={'collar_id': collar_id}
        )
        results['realtime'] = realtime_response
        
        # 2. Get pet plan
        plan_response = await self.api_client.get(
            session, 
            "v1/pet-plan", 
            params={'collar_id': collar_id}
        )
        results['pet_plan'] = plan_response
        
        # 3. Get timeline
        timeline_response = await self.api_client.get(
            session, 
            "v1/pet-timeline", 
            params={'collar_id': collar_id}
        )
        results['timeline'] = timeline_response
        
        return results
    
    async def simulate_user_feedback(self, session: aiohttp.ClientSession, event_id: str, feedback: str) -> Dict[str, Any]:
        """Simulate user submitting feedback"""
        return await self.api_client.post(
            session,
            "v1/submit-feedback",
            data={
                'event_id': event_id,
                'user_feedback': feedback,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

@pytest.fixture
def mobile_simulator(api_client):
    """Mobile app simulator fixture"""
    return MobileAppSimulator(api_client)

# Error scenario utilities
@pytest.fixture
def error_scenarios():
    """Common error scenarios for resilience testing"""
    return {
        'network_timeout': {
            'description': 'Network timeout simulation',
            'status_code': 408,
            'delay_ms': 30000
        },
        'server_error': {
            'description': 'Internal server error',
            'status_code': 500,
            'response': {'error': 'Internal server error'}
        },
        'rate_limit': {
            'description': 'Rate limit exceeded',
            'status_code': 429,
            'response': {'error': 'Rate limit exceeded'}
        },
        'authentication_failure': {
            'description': 'Authentication failure',
            'status_code': 401,
            'response': {'error': 'Invalid token'}
        },
        'invalid_data': {
            'description': 'Invalid request data',
            'status_code': 400,
            'response': {'error': 'Invalid collar_id'}
        }
    }

# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test"""
    yield
    # Cleanup logic would go here
    # For now, moto handles cleanup automatically
    pass