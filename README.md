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
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/kakashi3lite/Petty/main/docs/metrics/coverage.json)](https://github.com/kakashi3lite/Petty/actions/workflows/coverage.yml)

## 📖 Deep Dive Documentation

**For Pet Owners & Users:**  
🏠 [Consumer Overview](docs/CONSUMER_OVERVIEW.md) — What Petty does, privacy promises, FAQ

**For Developers & Contributors:**  
📱 [Mobile UI & Adaptive Polling](docs/MOBILE_UI_ADAPTIVE_POLLING.md) — Flutter implementation, glass UI, performance

## Quick Start

**Backend (30s):**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e .
python tests/validate_system.py
```

**Mobile (30s):**
```bash
cd mobile_app && flutter pub get && flutter run
```

**Dev Tools:**
```bash
make help        # See all commands
make py.test     # Run Python tests  
make flutter.analyze  # Flutter linting
```

## Core Features

* Behavior timeline + rules engine
* Secure telemetry storage (S3 + SSE)
* Privacy-by-design + data export tools
* Adaptive polling + glass UI
* Rate limiting + input validation

## License & Contribute

MIT — see `LICENSE`. PRs > complaints. Add tests. Keep it lean.

---
*Strategic details moved to deep dive docs above to keep README minimal.*


