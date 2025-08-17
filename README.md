# Petty — AI‑Powered Personalized Pet Care Platform

AI-driven behavior insights • Nutrition & care planning • Privacy-first telemetry • Secure, observable, extensible

---

## At a Glance

| Domain | Capability |
|--------|------------|
| Behavior Intelligence | Timeline generation, rule-based interpreter with safety guards |
| Personalization | Nutrition calculator, recommendation model scaffolding |
| Privacy & Security | PII redaction, coordinate precision limiting, rate limiting, circuit breaker fallbacks |
| Observability | Structured logging (JSON-friendly), future hooks for metrics/tracing |
| Mobile Experience | Flutter glassmorphism UI screens (Dashboard, Pet Profile, Tele‑Vet) |
| DevSecOps | CI (build/test), signing workflow, CodeQL, dependency updates (Dependabot), security digest generation |

Badges (populate once workflows complete):

```text
[![CI](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml/badge.svg)]()
[![CodeQL](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml/badge.svg)]()
[![Security Digest](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml/badge.svg)]()
```

---
## Architecture Overview

```text
 ┌────────────────────────────────────────┐
 │                Mobile                  │
 │  Flutter UI (Dashboard/Tele‑Vet/etc.)  │
 └───────────────────┬────────────────────┘
			│ REST / Event APIs
 ┌───────────────────▼────────────────────┐
 │          API / Lambda Layer            │
 │  (data_processor, timeline_generator,  │
 │   feedback_handler services)           │
 └───────────────┬───────────┬────────────┘
		   │           │
	┌────────▼───┐   ┌───▼────────┐
	│ AI Core /  │   │ Rule-based │
	│ Models     │   │ Behavioral │
	│ (reco, KB) │   │ Interpreter│
	└──────┬─────┘   └────┬───────┘
			   │  Enriched Events
	┌──────▼────────────────────────┐
	│   Output Sanitizers & Schemas │
	└──────┬────────────────────────┘
			   │ Secure Telemetry
	┌──────▼────────────────────────┐
	│   Storage / Streams (future)  │
	└───────────────────────────────┘
```

Key security & resilience layers wrap ingress (validators), processing (rate limiter, circuit breaker), and egress (output schemas, redaction).

---
\n## Security & Privacy

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
\n## Quick Start (Backend)

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
\n## Mobile (Flutter) Preview

Navigate to `mobile_app/` and use standard Flutter tooling:

```bash
cd mobile_app
flutter pub get
flutter run
```

---
\n## Development Workflow

1. Branch naming: `feat/*`, `fix/*`, `chore/*`, `sec/*`.
2. Open PR → CI runs (lint/tests/security). Auto labeling & TODO extraction workflow assists triage.
3. Merges to `main` trigger security digest artifact & (future) deploy workflow.

Pre-commit hooks configured in `.pre-commit-config.yaml` (install with `pre-commit install`).

---
\n## Testing Strategy

| Layer | Purpose |
|-------|---------|
| Unit / Validation | Schema constraints, redaction behavior |
| Security | OWASP LLM mitigation tests, AI misuse guard checks |
| Integration | End-to-end data flow across interpreter & timeline generation |
| Performance | Throughput & latency basic benchmarks |

Execute all: `python tests/run_tests.py`.

---
\n## Extending Models

Add new recommendation or behavior models in `src/` and register logic in the interpreter or a separate orchestration module. Keep transformations pure & validated.

---
\n## Observability

Structured logging located in `common/observability/logger.py`. Future enhancements: metrics (Prometheus), tracing (OpenTelemetry), correlation IDs.

---
\n## Roadmap

* [ ] Real JWT / OIDC auth integration
* [ ] SBOM + provenance (SLSA level goals)
* [ ] Enhanced anomaly detection model
* [ ] Containerization & Helm chart
* [ ] OpenTelemetry tracing + metrics
* [ ] Data retention & deletion API (privacy requests)
* [ ] Advanced recommendation personalization (hybrid CF+content)

---
\n## Contributing

1. Fork & branch.
2. Ensure tests pass and add new ones for changes.
3. Document public interfaces & update relevant docs.
4. Submit PR; ensure auto-label and CI pass.

---
\n## License

Add a chosen license file (e.g. Apache-2.0 or MIT) – not yet included.

---
\n## Disclaimer

Security / crypto / auth components include placeholder implementations and must be replaced or hardened before production deployment.

