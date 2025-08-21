# Production Readiness Implementation Plan

This document outlines the comprehensive changes needed to make the Petty project 100% production-ready.

## Overview

The Petty project currently has 6 critical blockers that prevent production deployment. This plan addresses each blocker with specific implementation details, security considerations, and testing strategies.

## Critical Blockers and Solutions

### 1. Authentication System Security Fix

**Current Issue**: Base64 token implementation in `src/common/security/auth.py` is insecure
**Solution**: Replace with production-grade JWT using `python-jose`

#### Implementation Details:
- Add `python-jose[cryptography]>=3.3.0` dependency (already in pyproject.toml)
- Implement proper JWT signing with RS256 algorithm
- Add token expiration, refresh token support
- Implement proper key rotation strategy
- Add comprehensive token validation

#### Security Features:
```python
# New TokenManager with proper JWT
class ProductionTokenManager:
    def __init__(self, private_key_path: str, public_key_path: str):
        # Load RSA keys from AWS Secrets Manager
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()
    
    def generate_token(self, user_id: str, scopes: List[str]) -> TokenPair:
        # Generate access token (15 min) and refresh token (7 days)
        # Include proper claims: iss, aud, exp, nbf, iat
        # Add custom claims for user_id and scopes
    
    def verify_token(self, token: str) -> TokenPayload:
        # Verify signature, expiration, and claims
        # Validate against revocation list
```

### 2. Observability Service Implementation

**Current Issue**: `src/common/observability/powertools.py` is referenced but missing
**Solution**: Implement comprehensive observability with AWS Lambda Powertools

#### Components:
1. **Structured Logging**
   - JSON formatted logs with correlation IDs
   - PII redaction for compliance
   - Log levels: DEBUG, INFO, WARN, ERROR
   - Custom fields: service_name, version, environment

2. **Metrics Collection**
   - Custom CloudWatch metrics for business KPIs
   - Performance metrics (latency, throughput)
   - Error rates and success rates
   - AI inference metrics (confidence scores, processing time)

3. **Distributed Tracing**
   - AWS X-Ray integration
   - Request tracing across services
   - Database query tracing
   - External API call tracing

#### Implementation:
```python
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger(service="petty-api")
tracer = Tracer(service="petty-api")
metrics = Metrics(namespace="Petty", service="api")

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    # Handler implementation with automatic observability
```

### 3. Secrets Management Implementation

**Current Issue**: No secure way to manage API keys, database credentials, JWT keys
**Solution**: Implement AWS Secrets Manager integration

#### Components:
1. **Secrets Client**
   - Centralized secrets retrieval
   - Caching with TTL
   - Automatic rotation support
   - Fallback mechanisms

2. **Secret Types**:
   - JWT signing keys (RSA key pair)
   - Database connection strings
   - Third-party API keys
   - Encryption keys for PII

#### Implementation:
```python
class SecretsManager:
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        # Check cache first
        # Retrieve from AWS Secrets Manager
        # Handle rotation scenarios
        # Update cache
```

### 4. API Versioning Strategy

**Current Issue**: No API versioning in infrastructure
**Solution**: Implement URL-based versioning with backward compatibility

#### Versioning Strategy:
- URL-based: `/v1/`, `/v2/` prefixes
- Header-based fallback: `API-Version: v1`
- Default to latest stable version
- Deprecation notices for old versions

#### Infrastructure Changes:
```yaml
# Add versioned paths to API Gateway
Events:
  IngestV1:
    Type: HttpApi
    Properties:
      Path: /v1/ingest
      Method: POST
  PetPlanV1:
    Type: HttpApi
    Properties:
      Path: /v1/pet-plan
      Method: GET
```

### 5. Mobile App Error Handling Enhancement

**Current Issue**: Generic exception handling with no retry logic
**Solution**: Implement robust error handling with exponential backoff

#### Error Types:
```dart
abstract class PettyException implements Exception {
  final String message;
  final int? statusCode;
  const PettyException(this.message, this.statusCode);
}

class NetworkException extends PettyException {
  const NetworkException(String message, int? statusCode) 
    : super(message, statusCode);
}

class AuthenticationException extends PettyException {
  const AuthenticationException(String message) : super(message, 401);
}

class ServerException extends PettyException {
  const ServerException(String message, int statusCode) 
    : super(message, statusCode);
}
```

#### Retry Logic:
```dart
class RetryPolicy {
  final int maxAttempts;
  final Duration initialDelay;
  final double backoffMultiplier;
  final List<int> retryableStatusCodes;
  
  const RetryPolicy({
    this.maxAttempts = 3,
    this.initialDelay = const Duration(milliseconds: 500),
    this.backoffMultiplier = 2.0,
    this.retryableStatusCodes = const [429, 500, 502, 503, 504],
  });
}
```

### 6. End-to-End Testing Suite

**Current Issue**: No comprehensive E2E tests
**Solution**: Implement full-stack testing covering mobile → API → AWS

#### Test Scenarios:
1. **Happy Path Flow**:
   - Mobile app starts up
   - Authentication succeeds
   - Real-time data loads
   - Timeline displays correctly
   - Feedback submission works

2. **Error Scenarios**:
   - Network failures
   - Authentication failures
   - API timeouts
   - Invalid data responses

3. **Performance Tests**:
   - Load testing with 1000+ concurrent users
   - AI inference latency under load
   - Database query performance

#### Implementation Structure:
```
tests/e2e/
├── conftest.py              # Test fixtures and setup
├── test_full_workflow.py    # Complete user journey
├── test_error_scenarios.py  # Error handling validation
├── test_performance.py      # Load and performance tests
└── utils/
    ├── mobile_simulator.py  # Mobile app simulation
    ├── api_client.py        # Test API client
    └── aws_helpers.py       # AWS service mocks/helpers
```

## Implementation Dependencies

### Python Dependencies to Add:
```toml
# Already in pyproject.toml but verify versions:
python-jose = ">=3.3.0"
aws-lambda-powertools = ">=2.25.0"
boto3 = ">=1.34.0"

# Additional for testing:
pytest-asyncio = ">=0.21.0"
aiohttp = ">=3.8.0"  # For async HTTP client
```

### Dart Dependencies to Add:
```yaml
dependencies:
  retry: ^3.1.2
  connectivity_plus: ^4.0.2
  
dev_dependencies:
  integration_test: ^1.0.0
  patrol: ^2.4.0  # For E2E testing
```

## Security Considerations

### Authentication Security:
- Use RSA-256 for JWT signing
- Implement proper key rotation (monthly)
- Add JWT blacklist for logout
- Rate limit authentication attempts
- Implement account lockout policies

### Data Protection:
- Encrypt sensitive data at rest
- Use TLS 1.3 for all communications
- Implement proper input validation
- Add comprehensive audit logging

### AWS Security:
- Use least privilege IAM roles
- Enable AWS CloudTrail
- Implement VPC endpoints for sensitive services
- Add AWS WAF rules for API protection

## Performance Requirements

### API Response Times:
- Real-time data: < 500ms (95th percentile)
- Timeline generation: < 2s (95th percentile)
- AI behavior analysis: < 5s (95th percentile)
- Feedback submission: < 1s (95th percentile)

### Scalability Targets:
- Support 10,000 concurrent users
- Process 100,000 collar data points/hour
- Handle 1,000 AI inferences/minute
- Store 1TB of time-series data

## Monitoring and Alerting

### Key Metrics:
- API latency (P50, P95, P99)
- Error rates by endpoint
- Authentication success/failure rates
- AI inference accuracy and confidence
- Database query performance
- Mobile app crash rates

### Alert Conditions:
- Error rate > 5% for 5 minutes
- API latency > 2s for 95th percentile
- Authentication failure rate > 20%
- Database connection failures
- AI inference confidence < 70%

## Rollout Strategy

### Phase 1: Core Security (Week 1)
1. Update authentication system
2. Implement secrets management
3. Add observability service
4. Update infrastructure

### Phase 2: Resilience (Week 2)
1. Enhanced mobile error handling
2. API versioning implementation
3. Performance optimizations
4. Security hardening

### Phase 3: Validation (Week 3)
1. End-to-end test suite
2. Load testing
3. Security penetration testing
4. Production deployment validation

## Success Criteria

### Security:
- [ ] All authentication uses cryptographically secure JWT
- [ ] No secrets in code or configuration files
- [ ] All PII properly redacted in logs
- [ ] OWASP LLM Top 10 mitigations verified

### Observability:
- [ ] All services emit structured logs
- [ ] Key metrics available in CloudWatch
- [ ] Distributed tracing operational
- [ ] Alerting covers all critical scenarios

### Reliability:
- [ ] Mobile app gracefully handles all error scenarios
- [ ] API supports versioning with backward compatibility
- [ ] End-to-end tests achieve 95% coverage
- [ ] Performance meets SLA requirements

This comprehensive plan ensures the Petty project will be fully production-ready with enterprise-grade security, observability, and reliability.