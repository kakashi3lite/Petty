# Petty — AI‑Powered Personalized Pet Care Platform 🐾

AI-driven behavior insights • Tail-ored nutrition & care planning • Privacy-first telemetry • Secure, observable, extensible.

> Sit. Stay. Deploy. Petty helps you ship features that make every pet parent say *“pawsome!”*

---

## At a Glance 🐶

| Domain | Capability |
|--------|------------|
| Behavior Intelligence | Timeline generation, rule-based interpreter with safety guards |
| Personalization | Nutrition calculator, recommendation model scaffolding |
| Privacy & Security | PII redaction, coordinate precision limiting, rate limiting, circuit breaker fallbacks |
| Observability | Structured logging (JSON-friendly), future hooks for metrics/tracing |
| Mobile Experience | Flutter glassmorphism UI screens (Dashboard, Pet Profile, Tele‑Vet) |
| DevSecOps | CI (build/test), signing workflow, CodeQL, dependency updates (Dependabot), security digest generation |

## Status & Quality 📊

[![CI](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml)
[![Coverage](https://codecov.io/gh/kakashi3lite/Petty/branch/main/graph/badge.svg)](https://codecov.io/gh/kakashi3lite/Petty)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/3d4e8f4d4c8e4a1b8f7e6d5c4b3a2f1e)](https://app.codacy.com/gh/kakashi3lite/Petty/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=kakashi3lite_Petty&metric=security_rating)](https://sonarcloud.io/dashboard?id=kakashi3lite_Petty)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![Security Digest](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml)

---

## Architecture Overview 🏗️

```text
 +--------------------------------------------------+
 |                    Mobile                        |
 |  Flutter UI (Dashboard • Tele‑Vet • Timeline)    |
 +--------------------------+-----------------------+
			    | REST / Event APIs
 +--------------------------v-----------------------+
 |               API / Lambda Layer                 |
 | data_processor • timeline_generator • feedback   |
 +-----------+----------------------+---------------+
			 |                      |
     +-------v------+        +------v---------+
     |   AI Core     |        | Behavioral    |
     |  (Reco / KB)  |        | Interpreter   |
     +-------+-------+        +------+--------+
	     |   Enriched Events     |
     +-------v-----------------------v-------+
     |     Output Sanitizers & Schemas       |
     +---------------+-----------------------+
					 | Secure Telemetry
	     +-------v-----------------------+
			 |  Storage / Streams (future)   |
	     +--------------------------------
```

Key security & resilience layers wrap ingress (validators), processing (rate limiter, circuit breaker), and egress (output schemas, redaction).

---



## Security & Privacy 🔐

See `docs/SECURITY.md` and `docs/PRIVACY.md` for full details. Highlights:

* Input Validation: Pydantic v2 models (`input_validators.py`) enforce bounds, patterns, timestamp sanity.
* Output Sanitization: `output_schemas.py` escapes / size limits event data.
* Rate Limiting & Circuit Breaking: Defensive wrappers with graceful fallback logic.
* Redaction: `redaction.py` scrubs PII (emails, basic secrets) prior to logging.
* Coordinate Precision Reduction: Mitigates exact location leakage (privacy-by-design).
* Authentication Stubs: `auth.py` placeholder token & API key management (swap with real JWT / OIDC provider).
* Crypto Utilities: `crypto_utils.py` hashing + token generation (pluggable for proper KMS / Vault in production).
* Supply Chain: Actions pinned to commit SHAs, Dependabot auto-updates, CodeQL static analysis.

Planned hardening (Roadmap): mTLS edge option, real JWT (RSA/ECDSA), SBOM export, SLSA provenance.

---



## Quick Start (Backend) 🚀

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -U pip
pip install -e .
python tests/validate_system.py
```

Run performance + security tests:

```bash
python tests/run_tests.py
```

---
\n## Mobile (Flutter) Preview 📱

Navigate to `mobile_app/` and use standard Flutter tooling:

```bash
cd mobile_app
flutter pub get
flutter run
```

---
\n## Development Workflow 🧪

1. Branch naming: `feat/*`, `fix/*`, `chore/*`, `sec/*`.
2. Open PR → CI runs (lint/tests/security). Auto labeling & TODO extraction workflow assists triage.
3. Merges to `main` trigger security digest artifact & (future) deploy workflow.

Pre-commit hooks configured in `.pre-commit-config.yaml` (install with `pre-commit install`).

---
\n## Testing Strategy 🧫

| Layer | Purpose |
|-------|---------|
| Unit / Validation | Schema constraints, redaction behavior |
| Security | OWASP LLM mitigation tests, AI misuse guard checks |
| Integration | End-to-end data flow across interpreter & timeline generation |
| Performance | Throughput & latency basic benchmarks |

Execute all: `python tests/run_tests.py`.

---
\n## Extending Models 🧠

Add new recommendation or behavior models in `src/` and register logic in the interpreter or a separate orchestration module. Keep transformations pure & validated.

---
\n## Observability 👀

Structured logging located in `common/observability/logger.py`. Future enhancements: metrics (Prometheus), tracing (OpenTelemetry), correlation IDs.

---

## Production Deployment 🚀

### Docker Deployment

```bash
# Clone repository
git clone https://github.com/kakashi3lite/Petty.git
cd Petty

# Copy environment configuration
cp .env.example .env
# Edit .env with your specific values

# Start production stack
docker-compose up -d

# Monitor deployment
docker-compose logs -f petty-api
```

### Kubernetes Deployment

```bash
# Build and push container
docker build -t ghcr.io/kakashi3lite/petty:latest .
docker push ghcr.io/kakashi3lite/petty:latest

# Deploy to Kubernetes (example)
kubectl apply -f k8s/
```

### Security Hardening

- **JWT Authentication**: Production RSA/ECDSA tokens with refresh rotation
- **Container Security**: Multi-stage builds, non-root user, read-only filesystem
- **Supply Chain**: SBOM generation, artifact signing with Cosign
- **Vulnerability Scanning**: Trivy, Bandit, Safety integrated in CI
- **SLSA Level 3**: Build provenance and attestation

### Monitoring Stack

- **Metrics**: Prometheus + Grafana dashboards
- **Tracing**: Jaeger OpenTelemetry integration  
- **Logs**: Structured JSON logging with correlation IDs
- **Health Checks**: Container and application-level monitoring

---

## Security Architecture 🔐

### Authentication & Authorization

```python
from src.common.security import create_token_pair, verify_jwt_token

# Create JWT token pair with refresh rotation
token_pair = create_token_pair(user_id="user123", scope="read:pets")

# Verify access token
payload = verify_jwt_token(token_pair.access_token)
```

### Data Protection

- **PII Redaction**: Automatic detection and masking
- **Encryption**: AES-256 for sensitive data at rest
- **Rate Limiting**: Configurable per-endpoint limits
- **Input Validation**: Schema-based validation with OWASP controls

---

## Roadmap 🗺️

### ✅ Completed
* [x] Real JWT authentication with RSA/ECDSA keys
* [x] SBOM generation with Syft and provenance (SLSA Level 3)
* [x] Docker multi-stage containerization
* [x] Comprehensive CI/CD with security scanning
* [x] Production monitoring stack (Prometheus, Grafana, Jaeger)
* [x] Coverage badges and Codacy integration
* [x] Container image signing with Cosign

### 🚧 In Progress  
* [ ] Enhanced anomaly detection model
* [ ] Containerization & Helm chart
* [ ] OpenTelemetry tracing + metrics
* [ ] Data retention & deletion API (privacy requests)
* [ ] Advanced recommendation personalization (hybrid CF+content)

---
\n## Contributing 🐕
Pull requests are welcome — no need to beg. Just make sure your changes pass tests and don’t introduce any “ruff” edges.

1. Fork & branch.
2. Ensure tests pass and add new ones for changes.
3. Document public interfaces & update relevant docs.
4. Submit PR; ensure auto-label and CI pass.

---
\n## License 📜

Add a chosen license file (e.g. Apache-2.0 or MIT) – not yet included.

---
\n## Disclaimer ⚠️

The security components have been enhanced for production readiness with RSA/ECDSA JWT authentication, refresh token rotation, and comprehensive vulnerability scanning. However, additional hardening may be required based on your specific deployment environment and threat model. Always review and test security configurations before production deployment.

---
\n## FAQ (Fur‑quently Asked Questions) 🐕‍🦺

**Why “Petty”?**  Because it’s pet-tech that refuses to compromise on quality.

**Is the AI model production-ready?**  Not yet — current logic is a structured rule engine with scaffolding for ML integration.

**Can I add my own model?**  Yes: drop into `src/` (e.g. `my_behavior_model.py`) and wire it through the interpreter or a new orchestrator.

**How do I keep secrets safe?**  Use environment variables + secret managers (AWS Secrets Manager, Vault) — never commit tokens.

**Why so many safety rails?**  Pets are family — reliability & privacy matter.

---
\n## Release Treats 🍖

We suggest semantic versioning: `MAJOR.MINOR.PATCH` — when breaking changes happen, bump like a startled cat.

