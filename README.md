# Petty 🐾

Smart wellness & behavior insights for your pet – in real time.

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](docs/PRODUCTION_READINESS_PLAN.md)
[![Security](https://img.shields.io/badge/Security-Enterprise-blue)](docs/SECURITY.md)

## Why Petty?

Pet owners want clear answers, not raw data. Petty turns collar + activity signals into plain‑language insights you can act on.

### What You Get

| Value | What It Means For You |
|-------|------------------------|
| Real‑time activity & behavior timeline | See when your pet is resting, active, unsettled, or showing notable patterns |
| Early wellness signals | Spot changes in routine that may warrant attention before they escalate |
| Personalized recommendations | Simple guidance (hydration, rest balance, enrichment prompts) – no jargon |
| Secure by design | Your pet’s data is encrypted, access‑controlled, and never sold |
| Transparent system health | Monitoring & alerts keep the service reliable so you aren’t guessing |
| Mobile + API | View on the app or integrate safely with your own tooling |

## Core Features (Live Today)

* Behavior & activity timeline (with feedback loop)
* Wellness signal interpretation (early anomalies surfaced)
* Secure feedback submission (owners add context)
* Lightweight nutrition & plan stubs (extensible)
* Mobile dashboard: status cards, recent behaviors, timeline
* Privacy & security guardrails: encryption, redaction, rate limiting
* Reliability: dead‑letter handling, monitoring, structured metrics

## Your Data, Protected

We treat pet + household context as sensitive.

* Encryption at rest & in transit
* Secrets isolated and rotated
* No secondary data monetization
* Personal identifiers redacted in logs

Read more: [`docs/SECURITY.md`](docs/SECURITY.md) | [`docs/PRIVACY.md`](docs/PRIVACY.md)

## Quick Peek (Developers / Integrators)

Want to run the stack locally:

```bash
python -m venv .venv
./.venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .
python tests/validate_system.py
```

Mobile app:

```bash
cd mobile_app
flutter pub get
flutter run
```

## Roadmap Snapshot

Planned next: richer nutrition modeling, proactive alert push, multi‑pet households, wellness scoring.

## Support & Feedback

Have an idea or found something confusing? Open an issue or submit feedback in‑app – we triage weekly.

## License

MIT — see `LICENSE`.

---
Focused on clear value for pet owners. Deeper architecture docs live in `docs/` for those who need them.


