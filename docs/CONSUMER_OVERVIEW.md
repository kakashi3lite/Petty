# Petty Consumer Overview

A concise, user-friendly explanation of Petty for pet owners and prospective adopters of the platform. This complements the engineering-centric repository.

## 1. What Is Petty?
Petty is an open, extensible system that helps you understand your pet's behavior, routine, and well‑being. It ingests telemetry from a smart collar or other sensors, interprets behavioral signals (restlessness, sleep quality, activity bursts), and can surface nutrition and care recommendations.

## 2. Core Benefits (Outcomes, Not Just Features)

| Benefit | What It Means for You |
|---------|-----------------------|
| Early Insight | Detect unusual inactivity or agitation sooner. |
| Peace of Mind | Continuous monitoring while you're away. |
| Tailored Care | Data‑driven nutrition & activity suggestions. |
| Privacy Control | You own the data; storage is transparent & deletable. |
| Extensible | Add new sensors or analytics without vendor lock‑in. |

## 3. High-Level Architecture (Plain Language)

1. Collar or sensor emits periodic telemetry (motion, temp, heart-rate proxy, location if available).
2. Ingestion service validates & stores raw events securely (server-side encryption in S3).
3. Behavioral interpreter models aggregate recent windows to classify patterns (rest / active / anomaly triggers).
4. Recommendation layer enriches with nutrition heuristics and historical baselines.
5. Mobile app polls adaptively (dynamic interval) to show fresh state without draining battery.

## 4. Quick Start (Self-Host) – Non-Engineer Friendly

| Step | Action |
|------|--------|
| 1 | Create a free AWS account (or use local moto for test). |
| 2 | Run deployment script to provision storage + minimal APIs. |
| 3 | Pair a supported collar (or start the simulator). |
| 4 | Open the mobile app (debug build) and point to your API base URL. |
| 5 | Observe live dashboard & alerts. |

## 5. Sample Telemetry Payload

```json
{
  "device_id": "collar-1234",
  "timestamp": "2025-08-17T12:30:05Z",
  "metrics": {
    "accel": {"x": 0.02, "y": -0.01, "z": 0.98},
    "activity_score": 63,
    "resting_heart_rate_proxy": 74,
    "temperature_c": 38.4
  },
  "battery_pct": 82,
  "firmware_version": "1.4.2",
  "seq": 45781
}
```

### Derived Behavioral Snapshot (Example)

```json
{
  "device_id": "collar-1234",
  "window_start": "2025-08-17T12:25:05Z",
  "window_end": "2025-08-17T12:30:05Z",
  "state": "ACTIVE_PLAY",
  "confidence": 0.87,
  "anomalies": []
}
```

## 6. Privacy & Data Control (3 Promises)

1. Encryption in transit and at rest (SSE-S3 AES256; BYO KMS optional roadmap).
2. Deterministic, user-owned buckets; easy script to export & delete data.
3. No hidden analytics beacons; only telemetry you explicitly send.

## 7. Battery & Network Efficiency

| Technique | Impact |
|----------|--------|
| Adaptive Polling | Reduces needless fetches when idle. |
| Jittered Scheduling | Avoids synchronized spikes + smooth server load. |
| Incremental Diffs (roadmap) | Minimize payload size vs full object repeats. |

## 8. Roadmap Snapshot

| Phase | Items |
|-------|-------|
| Near | Push streaming fallback, offline bundle cache, anomaly explanation UI. |
| Mid | ML-driven cadence tuning, multi-pet dashboard, caregiver sharing. |
| Future | Predictive health risk scoring, vet integration APIs. |

## 9. FAQ

| Question | Answer |
|----------|--------|
| What hardware is required? | Any BLE/WiFi collar sensor producing periodic motion/aux metrics; simulator provided. |
| Can I run without AWS? | Yes—local mode with moto & in-memory stores for test/dev. |
| Who owns the data? | You do—MIT license & self-hosting mean full control. |
| How often does it update? | Adaptive: 5s during active periods, up to ~45s when idle. |
| Is there a subscription? | No—open source; you pay only your own infra costs. |

## 10. Accessibility Commitments

- High contrast defaults; respects system dark mode.
- Supports dynamic text scaling (Flutter).
- Motion/blur reductions when user enables reduced motion.

## 11. Screenshots (Placeholders)

Add images here (e.g., `docs/media/dashboard_light.png`, `docs/media/dashboard_dark.png`).

## 12. How to Contribute (Consumer-Friendly)

Found a behavior mislabeled? Capture the raw telemetry window (export tool WIP) & open a GitHub issue with context (pet age, breed, activity situation).

---
Document version: 0.1 (initial consumer overview).
