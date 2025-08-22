# Observability Overview

This document explains how Petty implements production-grade observability with graceful degradation for local development.

## Goals

1. Fast root cause isolation (structured logs + correlation IDs)
2. Low overhead performance & behavior metrics
3. End-to-end traceability for critical request paths
4. Safe-by-default logging (redaction, length limits, sanitization)
5. Zero local friction: code runs even without cloud agents or Powertools

## Components

| Layer | Implementation (Cloud) | Local / Fallback | Notes |
|-------|------------------------|------------------|-------|
| Structured Logging | AWS Lambda Powertools Logger | Internal `StructuredLogger` | Auto redaction of sensitive keys |
| Tracing | AWS X-Ray (subsegments via Powertools Tracer) | No-op stub tracer | Disable with `DISABLE_TRACING=true` |
| Metrics | CloudWatch EMF (Powertools Metrics) | No-op stub metrics | Namespace: `Petty` |
| Correlation IDs | API Gateway / generated UUID | Generated UUID | Propagated via `obs_manager` |
| Business / AI Events | `ObservabilityManager.log_business_event` | Same API | Structured, versioned fields |
| Health Checks | `HealthChecker` | Same | Includes dependency probes |

## Fallback Design

`src/common/observability/powertools.py` attempts to import AWS Lambda Powertools. If unavailable:

- Stub classes (`_StubLogger`, `_StubTracer`, `_StubMetrics`) preserve public methods
- Decorators (`capture_lambda_handler`, `log_metrics`, `inject_lambda_context`) become no-ops
- The flag `POWertools_AVAILABLE` exposes runtime capability

This lets tests and local scripts run without container images or AWS credentials while keeping the production code path identical.

## Key APIs

```python
from src.common.observability.powertools import (
    logger, tracer, metrics, obs_manager,
    monitor_performance, log_api_request,
    lambda_handler_with_observability, health_checker,
    POWertools_AVAILABLE
)
```

### Business / Security Events

```python
obs_manager.log_business_event("behavior_interpreted", behavior="restless", confidence=0.82)
obs_manager.log_security_event("rate_limit_triggered", severity="medium", details={"collar_id": "SN-123"})
```

### Performance / Tracing

```python
@monitor_performance("nutrition_calc")
def calculate():
    ...

with obs_manager.trace_operation("timeline_build", {"items": 42}):
    build_timeline()
```

### Lambda Handler Wrapper

```python
@lambda_handler_with_observability
def handler(event, context):
    return {"statusCode": 200, "body": "ok"}
```

## Logging Safety

- Emojis & non-BMP chars stripped automatically on Windows (console encoding guard)
- Message length constrained to prevent log flooding
- Sensitive key patterns (`token`, `secret`, `password`, etc.) redacted
- Newlines and control characters removed to mitigate injection

## Metrics Conventions

| Metric | Unit | Description |
|--------|------|-------------|
| `<operation>_duration` | Milliseconds | Latency per monitored operation |
| `<operation>_count` | Count | Invocation count |
| `<operation>_errors` | Count | Error occurrences (only emitted when failures happen) |
| `ai_inference_confidence` | Percent | Model confidence per inference |
| `ai_inference_duration` | Milliseconds | Time spent in AI inference |
| `ai_inference_count` | Count | Inference invocation count |

## Tracing Strategy

Only high-value boundaries are traced to minimize noise and cost:

- API entry points
- Lambda handler lifecycle
- Expensive domain operations (timeline generation, interpretation, nutrition calculations)

Subsegment metadata is limited to small, structured dictionaries (`operation_metadata`). Large payloads are avoided to reduce trace storage size.

## Health Checks

`HealthChecker` exposes two methods:

- `get_health_status()` – static service / uptime info
- `check_dependencies()` – lightweight reachability checks (S3, Timestream)

Integrate into a `/health` route or operational Lambda as needed.

## Environment Flags

| Variable | Effect |
|----------|--------|
| `SERVICE_NAME` | Service identity in logs / metrics |
| `LOG_LEVEL` | Logging verbosity (default INFO) |
| `DISABLE_TRACING` | If `true`, disables tracer (still safe) |
| `DISABLE_UNICODE_LOGS` | If `1`, forces ASCII logging |
| `METRICS_NAMESPACE` | Override metrics namespace |

## Verification

Run the production readiness validator:

```bash
python tests/validate_production_readiness.py
```

Expect observability section to pass with either real Powertools or stubs.

## Future Enhancements

- OpenTelemetry exporter (conditional) for richer distributed tracing
- Dynamic sampling based on error rate
- Structured event schema version field & registry
- Metrics dimensionality expansion (environment, version tags)

---
Lean, safe, and degradable observability: production confidence without local friction.
