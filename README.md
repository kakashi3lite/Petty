# Petty 🐾

Minimal. Opinionated. Treat‑driven.

```text
UEVUVFk6IEFJICsgYmVoYXZpb3IgK2NhcmUgKyBwcml2YWN5LWJ5LWRlc2lnbiArIG9ic2VydmFiaWxpdHk=
```
Decode me later; caffeine first.

## Badges

[![CI](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml)
[![Security Tasks](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml)
[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen)](docs/PRODUCTION_READINESS_PLAN.md)
[![Enterprise Security](https://img.shields.io/badge/Security-Enterprise-blue)](docs/SECURITY.md)

Extended docs live off‑page: [Consumer Overview](docs/CONSUMER_OVERVIEW.md) • [Mobile UI Notes](docs/MOBILE_UI_ADAPTIVE_POLLING.md) • [Production Readiness](docs/PRODUCTION_READINESS_PLAN.md) • [Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)

## What Actually Exists (Today)

* **NEW:** ✅ Production-grade security with RSA-256 JWT, secrets management, and data encryption
* **NEW:** ✅ Comprehensive observability with AWS Lambda Powertools (metrics, logging, tracing)
* **NEW:** ✅ API versioning strategy with `/v1/` endpoints and backward compatibility
* **NEW:** ✅ Mobile app error handling with retry logic, exponential backoff, and circuit breakers
* **NEW:** ✅ Complete E2E testing suite covering user journeys, error scenarios, and performance
* **NEW:** ✅ CloudWatch alarms for high error rates and latency with DLQ for failed invocations
* **NEW:** ✅ Detailed production deployment guide and readiness validation tools
* **NEW:** ✅ Adaptive polling with debounced stream utility for mobile UI
* Behavior timeline fetch + feedback ingestion (S3, SSE‑S3, retries)
* Lightweight nutrition & plan stubs (replace later with real modeling)
* Validation + redaction + rate limiting layer around Lambda handlers
* Flutter screens: Dashboard, Pet Profile, Tele‑Vet
* Makefile + CI pipeline (lint, tests, coverage to Codecov, CodeQL, security chores)

## Quickstart: Backend (≈30s)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -U pip && pip install -e .
python tests/validate_system.py
```

## Quickstart: Mobile

```bash
cd mobile_app
flutter pub get
flutter run
```

## Dev Loop

```bash
make py.lint  # Run linting checks
make py.test  # Run unit and integration tests
make flutter.analyze  # Analyze Flutter code
python tests/validate_production_readiness.py  # Validate production features
```

## Security Bits

* **NEW:** RSA-256 JWT with proper token expiration, refresh tokens, and revocation
* **NEW:** AWS Secrets Manager integration with local encryption and TTL caching
* **NEW:** CloudWatch monitoring and alerting for security events
* **NEW:** PII encryption and redaction for compliance (GDPR/CCPA/HIPAA ready)
* Input validators, output schemas, redaction, rate limiter
* Dependency & static analysis (CodeQL), plus S3 SSE‑S3
* Least privilege IAM roles with fine-grained permissions

Full details in [Security Documentation](docs/SECURITY.md)

## Contributing

PRs > complaints. Ship tests. Keep secrets out. Trim scope mercilessly.

## Production Deployment

For detailed production deployment instructions, see the [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md).

```bash
# Deploy to staging environment
sam build
sam deploy --parameter-overrides Environment=staging

# Deploy to production (after validation)
sam deploy --parameter-overrides Environment=production
```

## License

MIT — see `LICENSE`.

## Bonus Base64

```text
U2l0LiBTdGF5LiBEZXBsb3kuIEFkdmljZSB5b3VyIHBldCdzIGh1bWFuLg==
```
Decode if you must; your pet still wants a walk.

---
Future work tracked in issues / PR descriptions. README stays lean.


