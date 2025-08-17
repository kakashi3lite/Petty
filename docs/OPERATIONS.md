# Operations Guide

## Where to find coverage & logs

### Coverage Reports

- **Live Coverage Dashboard**: [Codecov](https://codecov.io/gh/kakashi3lite/Petty)
- **Local Coverage**: Run `pytest --cov=src --cov-report=html` and open `htmlcov/index.html`
- **CI Coverage**: Available as artifacts in [GitHub Actions runs](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)

### CloudWatch Log Groups

Quick links to AWS CloudWatch log groups for monitoring and debugging:

- **Data Processor Function**: `/aws/lambda/DataProcessorFunction`
- **Alert Engine**: `/aws/lambda/AlertEngine`
- **Authentication Service**: `/aws/lambda/AuthService`
- **API Gateway**: `/aws/apigateway/PettyAPI`

*Note: Replace with actual log group names when deployed to your AWS environment.*

### Re-running Golden Tests

To regenerate golden test files (reference outputs for regression testing):

```bash
# Re-run all golden tests and update reference files
pytest tests/ -k "golden" --update-goldens

# Re-run specific golden test category
pytest tests/integration/test_behavior_analysis.py --update-goldens

# Verify golden tests without updating
pytest tests/ -k "golden"
```

### Test Configuration

**Test Isolation**: 
- **Environment Variable**: `PYTEST_ISOLATION=strict` (default) enables test isolation mode
- **Override**: Set `PYTEST_ISOLATION=standard` to disable strict isolation
- **Purpose**: Prevents test pollution and ensures deterministic test execution

```bash
# Run with strict isolation (default)
pytest tests/

# Run with standard isolation (if needed for debugging)
PYTEST_ISOLATION=standard pytest tests/

# Run specific tests with isolation override
PYTEST_ISOLATION=standard pytest tests/test_specific_module.py
```

### Performance Monitoring

- **Response Times**: Monitor via CloudWatch custom metrics
- **Error Rates**: Available in CloudWatch dashboard
- **Resource Usage**: Lambda execution metrics in CloudWatch