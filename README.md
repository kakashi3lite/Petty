# Petty 🐾

Minimal. Opinionated. Treat‑driven.

```text
UEVUVFk6IEFJICsgYmVoYXZpb3IgK2NhcmUgKyBwcml2YWN5LWJ5LWRlc2lnbiArIG9ic2VydmFiaWxpdHk=
```
Decode me later; caffeine first.

## Badges

[![CI](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)
[![Coverage](https://github.com/kakashi3lite/Petty/actions/workflows/coverage.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/coverage.yml)
[![codecov](https://codecov.io/gh/kakashi3lite/Petty/branch/main/graph/badge.svg)](https://codecov.io/gh/kakashi3lite/Petty)
[![CodeQL](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml)
[![Security Tasks](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/dev-tasks.yml)

Extended docs live off‑page: [Consumer Overview](docs/CONSUMER_OVERVIEW.md) • [Mobile UI Notes](docs/MOBILE_UI_ADAPTIVE_POLLING.md)

## What Actually Exists (Today)

* Behavior timeline fetch + feedback ingestion (S3, SSE‑S3, retries)
* Lightweight nutrition & plan stubs (replace later with real modeling)
* Validation + redaction + rate limiting layer around Lambda handlers
* Flutter screens: Dashboard, Pet Profile, Tele‑Vet (static polling loop for now)
* Makefile + CI pipeline (lint, tests, coverage to Codecov, CodeQL, security chores)

Not yet (being honest): adaptive polling debounce utility, KMS encryption option, help/FAQ screen, golden tests, telemetry export & sample generator.

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

make py.lint • make py.test • make flutter.analyze

## Security Bits

Input validators, output schemas, redaction, rate limiter, dependency & static analysis (CodeQL), plus S3 SSE‑S3.

## Contributing

PRs > complaints. Ship tests. Keep secrets out. Trim scope mercilessly.

## How Coverage Works

Coverage is tracked across both Python backend and Flutter mobile app:

* **Python Coverage**: Uses pytest-cov to generate XML and HTML reports, targeting 85% minimum coverage
* **Flutter Coverage**: Uses `flutter test --coverage` to generate LCOV reports  
* **Upload**: Both reports are uploaded to [Codecov](https://codecov.io/gh/kakashi3lite/Petty) via dedicated coverage workflow
* **CI Integration**: Coverage runs on every push/PR and provides diff coverage analysis
* **Local Testing**: Run `make py.test` for Python or `flutter test --coverage` in mobile_app/ for Flutter

View detailed coverage reports at [codecov.io/gh/kakashi3lite/Petty](https://codecov.io/gh/kakashi3lite/Petty).

## License

MIT — see `LICENSE`.

## Bonus Base64

```text
U2l0LiBTdGF5LiBEZXBsb3kuIEFkdmljZSB5b3VyIHBldCdzIGh1bWFuLg==
```
Decode if you must; your pet still wants a walk.

---
Future work tracked in issues / PR descriptions. README stays lean.


