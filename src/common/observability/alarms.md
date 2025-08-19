# CloudWatch Alarms Configuration

This document defines the alarm thresholds and automated mitigation strategies for the Petty pet monitoring system.

## Alarm Categories

### Application Performance Alarms

#### API Gateway Error Rate
- **Metric**: `4XXError` and `5XXError` from API Gateway
- **Threshold**: 
  - Warning: > 5% error rate over 5 minutes
  - Critical: > 15% error rate over 3 minutes
- **Action**: 
  - Warning: Set SAFE_MODE to ELEVATED
  - Critical: Set SAFE_MODE to CRITICAL

#### Lambda Function Duration
- **Metric**: `Duration` from Lambda functions
- **Threshold**:
  - Warning: > 10 seconds average over 5 minutes
  - Critical: > 15 seconds average over 3 minutes
- **Action**:
  - Warning: Enable heavy route throttling
  - Critical: Set SAFE_MODE to CRITICAL

#### Lambda Function Errors
- **Metric**: `Errors` from Lambda functions
- **Threshold**:
  - Warning: > 5 errors per minute
  - Critical: > 20 errors per minute
- **Action**:
  - Warning: Set SAFE_MODE to ELEVATED
  - Critical: Set SAFE_MODE to CRITICAL

#### Lambda Function Throttles
- **Metric**: `Throttles` from Lambda functions
- **Threshold**:
  - Warning: > 0 throttles per minute
  - Critical: > 5 throttles per minute
- **Action**:
  - Warning: Set SAFE_MODE to ELEVATED
  - Critical: Set SAFE_MODE to EMERGENCY

### Infrastructure Alarms

#### Timestream Write Throttles
- **Metric**: `UserErrors` from Timestream
- **Threshold**:
  - Warning: > 5 throttles per minute
  - Critical: > 20 throttles per minute
- **Action**:
  - Warning: Enable heavy route throttling
  - Critical: Set SAFE_MODE to CRITICAL

#### High Memory Usage
- **Metric**: `MemoryUtilization` from Lambda
- **Threshold**:
  - Warning: > 80% average over 5 minutes
  - Critical: > 95% average over 3 minutes
- **Action**:
  - Warning: Set SAFE_MODE to ELEVATED
  - Critical: Set SAFE_MODE to CRITICAL

### Security Alarms

#### Rate Limiting Violations
- **Metric**: Custom metric from rate limiter
- **Threshold**:
  - Warning: > 100 violations per minute
  - Critical: > 500 violations per minute
- **Action**:
  - Warning: Set SAFE_MODE to ELEVATED
  - Critical: Set SAFE_MODE to CRITICAL

#### Authentication Failures
- **Metric**: Custom metric from auth module
- **Threshold**:
  - Warning: > 50 failures per minute
  - Critical: > 200 failures per minute
- **Action**:
  - Warning: Enable enhanced monitoring
  - Critical: Set SAFE_MODE to CRITICAL

## Safe Mode Levels and Actions

### NORMAL
- **Rate Limit Multiplier**: 1.0 (no throttling)
- **Max Concurrent Requests**: 100
- **Heavy Route Throttling**: Disabled
- **GitHub Issue Creation**: Disabled

### ELEVATED
- **Rate Limit Multiplier**: 0.7 (30% throttling)
- **Max Concurrent Requests**: 70
- **Heavy Route Throttling**: Enabled (429 responses for heavy routes)
- **GitHub Issue Creation**: Enabled
- **Monitoring**: Enhanced logging and metrics

### CRITICAL
- **Rate Limit Multiplier**: 0.3 (70% throttling)
- **Max Concurrent Requests**: 30
- **Heavy Route Throttling**: Enabled (429 responses for heavy routes)
- **GitHub Issue Creation**: Enabled with high priority
- **Monitoring**: All requests logged, real-time alerting

### EMERGENCY
- **Rate Limit Multiplier**: 0.1 (90% throttling)
- **Max Concurrent Requests**: 10
- **Heavy Route Throttling**: Enabled (429 responses for all non-essential routes)
- **GitHub Issue Creation**: Enabled with critical priority
- **Monitoring**: Full debug logging, immediate escalation

## Heavy Routes Definition

Heavy routes are endpoints that consume significant resources:

1. `/pet-timeline` - Timeline generation with ML analysis
2. `/ingest` - High-volume data processing
3. `/submit-feedback` - Complex feedback processing

## Automated Mitigation Actions

### Step 1: Immediate Response (< 30 seconds)
1. Set appropriate SAFE_MODE level
2. Apply rate limiting and throttling
3. Enable enhanced monitoring

### Step 2: Documentation (< 2 minutes)
1. Create GitHub issue with:
   - Alarm details and timeline
   - Links to CloudWatch dashboards
   - Current system metrics
   - Recommended actions

### Step 3: Recovery Monitoring (ongoing)
1. Monitor system recovery metrics
2. Gradual safe mode level reduction
3. Post-incident analysis and documentation

## Recovery Procedures

### Automatic Recovery
- Monitor for sustained improvement (> 10 minutes)
- Gradually reduce safe mode level
- EMERGENCY → CRITICAL → ELEVATED → NORMAL

### Manual Override
- Operators can manually adjust safe mode via environment variables
- Emergency procedures for immediate system recovery
- Manual GitHub issue creation for complex incidents

## GitHub Issue Template

When alarms trigger, the following information is automatically included:

```markdown
# System Alert: [Alarm Name]

## Incident Summary
- **Alert Time**: [timestamp]
- **Severity**: [Warning/Critical]
- **Safe Mode Level**: [current level]

## Metrics
- **Error Rate**: [current rate]
- **Response Time**: [current average]
- **Throughput**: [current RPS]

## Dashboard Links
- [CloudWatch Dashboard](link)
- [Application Logs](link)
- [Infrastructure Metrics](link)

## Automatic Actions Taken
- [List of mitigation actions]

## Manual Actions Required
- [If any manual intervention needed]
```

## Monitoring and Alerting

All alarms are configured with:
- SNS topic notifications
- CloudWatch dashboard integration
- Automated Step Functions execution
- Real-time metric streaming

## Testing and Validation

Regular testing includes:
- Chaos engineering scenarios
- Load testing with alarm validation
- Manual safe mode testing
- Recovery time measurement