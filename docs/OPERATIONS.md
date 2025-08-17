# Operations Guide

Operational documentation for the Petty serverless pet monitoring system.

## CloudWatch Logs & Metrics

### Lambda Function Logs

Access logs via AWS CloudWatch console or CLI:

```bash
# Data Processor Function
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/petty-DataProcessorFunction"

# Timeline Generator Function  
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/petty-TimelineGeneratorFunction"

# Feedback Handler Function
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/petty-FeedbackHandlerFunction"
```

### Key Metrics to Monitor

- **Lambda Duration**: Function execution time
- **Lambda Errors**: Error count and rate
- **Lambda Throttles**: Concurrency throttling events
- **API Gateway 4xx/5xx**: Client and server errors
- **Timestream Write Throttles**: Database write capacity issues

### CloudWatch Dashboards

Create custom dashboards monitoring:
- Request volume by endpoint (`/ingest`, `/pet-timeline`, `/submit-feedback`)
- Error rates across all Lambda functions
- Timestream write throughput and error rates
- S3 feedback bucket object counts

## Coverage URLs & CI Status

### Test Coverage

- **Codecov Dashboard**: `https://codecov.io/github/kakashi3lite/Petty`
- **Local Coverage Reports**: Generated in `htmlcov/` after running `pytest --cov`

### CI Workflow Status

- **Main CI Pipeline**: [GitHub Actions CI Workflow](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)
- **Security Scanning**: [Security Workflow](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml)
- **CodeQL Analysis**: [CodeQL Workflow](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml)

### Build Artifacts

CI generates the following artifacts:
- `python-test-results`: JUnit XML, coverage reports
- `security-reports`: Bandit, Safety, Semgrep output
- `sbom-artifacts`: Software Bill of Materials
- `flutter-test-results`: Mobile app test coverage

## Golden Updates & Property-Based Testing

### Property-Based Test Categories

Run property-based tests that validate system invariants:

```bash
# Run all property-based tests (marked with @pytest.mark.property)
pytest tests/ -m "property" --hypothesis-profile=ci -v

# Run specific property test suites
pytest tests/security/test_ai_security.py::TestModelRobustness::test_privacy_preservation_property -v
pytest tests/security/test_owasp_llm_mitigations.py::TestInputSanitization::test_text_sanitization_property -v
```

### Golden Test Data Updates

When model behavior changes, update golden test datasets:

1. **Backup existing datasets**: `cp tests/fixtures/golden_* tests/fixtures/backup/`
2. **Regenerate with new model**: `python tests/generate_golden_data.py`
3. **Validate changes**: Review diffs before committing
4. **Update baselines**: Commit new golden datasets after validation

## Timestream Queries

### Common Operational Queries

#### Recent Collar Activity (Last 24 Hours)
```sql
SELECT collar_id, time, heart_rate, activity_level, location
FROM "PettyDB"."CollarMetrics" 
WHERE time > ago(24h)
ORDER BY time DESC
LIMIT 1000
```

#### High Activity Detection
```sql
SELECT collar_id, time, heart_rate, activity_level
FROM "PettyDB"."CollarMetrics"
WHERE time > ago(1h) 
  AND activity_level > 2
  AND heart_rate > 120
ORDER BY time DESC
```

#### Collar Health Check (Missing Data)
```sql
SELECT collar_id, max(time) as last_seen
FROM "PettyDB"."CollarMetrics"
WHERE time > ago(6h)
GROUP BY collar_id
HAVING max(time) < ago(30m)
ORDER BY last_seen ASC
```

#### Aggregated Activity by Hour
```sql
SELECT 
  bin(time, 1h) as hour_bucket,
  collar_id,
  avg(heart_rate) as avg_heart_rate,
  avg(activity_level) as avg_activity
FROM "PettyDB"."CollarMetrics"
WHERE time > ago(24h)
GROUP BY bin(time, 1h), collar_id
ORDER BY hour_bucket DESC
```

### Query Performance Tips

- Use time-based filters to leverage Timestream's time-series optimization
- Limit result sets with appropriate `LIMIT` clauses
- Use `bin()` function for time-based aggregations
- Monitor query costs in CloudWatch

## Incident Response

### Common Issues

**High Lambda Duration**
- Check CloudWatch logs for timeout errors
- Review recent code deployments
- Verify external service dependencies (Timestream, S3)

**Timestream Write Errors**
- Check write capacity metrics
- Validate data format in ingestion pipeline
- Review IAM permissions for Lambda execution role

**Missing Collar Data**
- Run collar health check query above
- Check API Gateway access logs for failed requests
- Verify collar authentication tokens

### Escalation Contacts

- **Primary**: Engineering Team (GitHub Issues)
- **Security Issues**: Follow [SECURITY.md](SECURITY.md) incident response
- **AWS Account Issues**: Infrastructure team via internal escalation

## Monitoring Runbooks

### Daily Health Checks

1. Review CloudWatch dashboard for anomalies
2. Check CI pipeline status and test coverage trends
3. Run collar health check Timestream query
4. Verify S3 feedback bucket permissions and usage

### Weekly Reviews

1. Analyze property-based test failure trends
2. Review security scan results from CI artifacts
3. Check Timestream storage costs and retention policies
4. Update golden test datasets if model behavior changed

---
For additional operational procedures, see the [SECURITY.md](SECURITY.md) incident response plan.