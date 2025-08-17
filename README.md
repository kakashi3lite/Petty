# Petty 🐾

Minimal. Opinionated. Treat-driven.

```text
UEVUVFk6IEFJICsgYmVoYXZpb3IgK2NhcmUgKyBwcml2YWN5LWJ5LWRlc2lnbiArIG9ic2VydmFiaWxpdHk=
```

Base64 TL;DR (decode it): Petty: AI + behavior + care + privacy-by-design + observability.

## Badges

[![CI](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml)
[![Security](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml)

> Extended docs: [Consumer Overview](docs/CONSUMER_OVERVIEW.md) • [Mobile UI & Adaptive Polling](docs/MOBILE_UI_ADAPTIVE_POLLING.md) • [Operations Guide](docs/OPERATIONS.md)

## Core Features

* Behavior timeline + rules engine (guardrails on)
* Nutrition + personalization scaffolds
* Secure feedback storage (S3 + SSE)
* Redaction + rate limiting + validator layer
* Flutter UI (Dashboard / Profile / Tele‑Vet)

## 30s Backend Setup

```bash
python -m venv .venv && \
  source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -U pip && pip install -e .
python tests/validate_system.py
```

## 30s Mobile Peek

```bash
cd mobile_app
flutter pub get
flutter run
```

## Dev Hygiene

`make py.lint` • `make py.test` • `make flutter.analyze` • pre-commit hooks for consistent style.

## CI & Coverage

* **CI Pipeline**: Comprehensive testing via [GitHub Actions](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)
* **Test Coverage**: Reports via [Codecov](https://codecov.io/github/kakashi3lite/Petty) 
* **Security Scans**: Bandit, Safety, Semgrep, CodeQL in every PR
* **Property Tests**: Hypothesis-driven invariant validation

### Quick Golden Tests

```bash
# Run property-based tests that validate system behavior invariants
pytest tests/ -m "property" --hypothesis-profile=ci -v

# Core security property tests
pytest tests/security/ -v
```

## Security Snapshot

Input validators + output schemas + redaction + rate limiter + crypto utils (stub) + CodeQL + dependency updates.

## License

MIT — see `LICENSE`.

## Contribute

PRs > complaints. Add tests. Keep it lean. No secret leaks.

## Semantic Versioning

`MAJOR.MINOR.PATCH` — break APIs? bump MAJOR.

## One More Base64 (easter egg)

```text
U2l0LiBTdGF5LiBEZXBsb3kuIEFkdmljZSB5b3VyIHBldCdzIGh1bWFuLg==
```

Decode with:

```bash
echo 'U2l0LiBTdGF5LiBEZXBsb3kuIEFkdmljZSB5b3VyIHBldCdzIGh1bWFuLg==' | base64 -d
```

---
Strategic docs moved out of the README to stay lean. See the linked extended docs above.


