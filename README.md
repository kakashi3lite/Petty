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
| Mobile Experience | Flutter glassmorphism UI with Material 3, adaptive polling (15s base), auto-dispose lifecycle, real-time dashboard with feedback system |
| DevSecOps | CI (build/test), signing workflow, CodeQL, dependency updates (Dependabot), security digest generation |

**Workflow Status:**

[![CI](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml/badge.svg)](https://github.com/kakashi3lite/Petty/actions/workflows/codeql.yml)
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

Key security & resilience layers wrap ingress (validators), processing (rate limiter, circuit breaker), and egress (output schemas, redaction). Mobile layer employs early Riverpod selective rebuild pattern; adaptive polling (ETag/backoff) planned.

---

## Mobile UI Theming & Glassmorphism 🎨

### Design Philosophy

Petty's mobile interface embraces **glassmorphism** combined with **Material 3** design principles to create an elegant, modern user experience that feels both sophisticated and pet-friendly.

### Glassmorphism Implementation

Our glassmorphism design uses a custom `GlassContainer` widget that provides:

**Visual Properties:**
- **Backdrop Blur**: `ImageFilter.blur(sigmaX: 14, sigmaY: 14)` creates the frosted glass effect
- **Transparency**: `Colors.white.withOpacity(0.12)` for subtle background translucency
- **Border Highlight**: `Colors.white.withOpacity(0.2)` creates the characteristic glass edge glow
- **Border Radius**: Configurable radius (default 20px) for smooth, rounded corners

**Design Tokens:**
```dart
// Glass Container Default Values
BorderRadius: 20px
BackdropBlur: 14px (sigma X/Y)
Background: White 12% opacity
Border: White 20% opacity, 1px width
Padding: 16px (configurable)
```

### Material 3 Integration

**Color Scheme:**
- **Primary Gradient**: Ocean blue to cyan (`Color(0xFF2193b0)` → `Color(0xFF6dd5ed)`)
- **Text Hierarchy**: White primary, white70 secondary for optimal contrast on gradient backgrounds
- **Interactive Elements**: Green accent for positive feedback, red accent for negative feedback

**Typography Scale:**
- **Headlines**: `headlineMedium` for screen titles
- **Metrics**: `titleLarge` with bold weight for key data points
- **Labels**: `titleMedium` for secondary information
- **Timestamps**: 12px with 70% opacity for subtle context

### Component Architecture

**GlassContainer Usage Patterns:**
```dart
// Metric cards with consistent spacing
GlassContainer(
  child: _Metric(
    label: 'Heart Rate', 
    value: '$hr BPM', 
    icon: Icons.favorite
  )
)

// Timeline events with interactive feedback
GlassContainer(
  child: Row(children: [
    // Event content
    // Feedback buttons (thumbs up/down)
  ])
)
```

**Responsive Design:**
- **Padding**: Consistent 16px padding throughout for finger-friendly touch targets
- **Spacing**: 12px between metric cards, 16px for major sections
- **Safe Area**: All content respects device safe areas and notches

### Accessibility Considerations

- **Contrast Ratios**: White text on gradient backgrounds maintains WCAG AA compliance
- **Touch Targets**: Minimum 44px for all interactive elements
- **Visual Hierarchy**: Clear distinction between primary and secondary information
- **Focus States**: Material 3 focus indicators for keyboard navigation

### Future Enhancements

- **Dark Mode**: Adaptive glass containers with darker tints
- **Dynamic Colors**: Material You integration for system-aware theming  
- **Custom Glass Variants**: Different blur intensities for information hierarchy
- **Animation Tokens**: Consistent motion design across glass elements

---

## Adaptive Polling Plan 📡

### Current Implementation

Petty implements a **smart polling strategy** that balances real-time responsiveness with battery efficiency and network conservation.

### Polling Architecture

**Base Polling Strategy:**
```dart
static final _realTimeProvider = StreamProvider.autoDispose<Map<String, dynamic>>((ref) async* {
  const pollInterval = Duration(seconds: 15); // Natural debounce >=12s
  while (true) {
    try {
      final data = await service.getRealTimeData(_collarId);
      yield data;
    } catch (e) {
      yield {"error": e.toString()};
    }
    await Future.delayed(pollInterval);
  }
});
```

**Key Features:**
- **15-second base interval**: Balances responsiveness with battery conservation
- **Auto-dispose**: Riverpod automatically stops polling when screen is disposed
- **Error Resilience**: Graceful error handling with fallback data
- **Debounce Protection**: Natural >=12s debounce prevents excessive API calls

### Adaptive Strategies

**Current Implemented:**
1. **Screen Lifecycle Management**: Polling automatically stops when dashboard is disposed
2. **Error Recovery**: Failed requests don't break the polling loop
3. **Data Caching**: Riverpod providers cache latest successful responses

**Planned Enhancements:**

**Dynamic Interval Adjustment:**
```dart
// Planned implementation
class AdaptivePollingStrategy {
  Duration getPollingInterval({
    required BatteryLevel battery,
    required NetworkType network,
    required AppLifecycleState lifecycle,
  }) {
    // Fast polling on WiFi + good battery
    if (network == NetworkType.wifi && battery > 50) {
      return Duration(seconds: 10);
    }
    // Slower on cellular or low battery
    if (network == NetworkType.cellular || battery < 20) {
      return Duration(seconds: 30);
    }
    return Duration(seconds: 15); // default
  }
}
```

### ETag Implementation Plan

**Cache-Aware Polling:**
```dart
// Future implementation
class ETagPollingService {
  String? _lastETag;
  
  Future<PetData?> pollWithETag() async {
    final headers = _lastETag != null 
      ? {'If-None-Match': _lastETag!}
      : <String, String>{};
      
    final response = await http.get(endpoint, headers: headers);
    
    if (response.statusCode == 304) {
      return null; // No change, use cached data
    }
    
    _lastETag = response.headers['ETag'];
    return PetData.fromJson(response.body);
  }
}
```

### Battery Optimization

**Lifecycle-Aware Polling:**
- **Foreground**: Full 15s polling for active monitoring
- **Background**: Reduced to 60s intervals (when supported)
- **Screen Off**: Minimal polling or push notification fallback

**Network-Aware Adjustments:**
- **WiFi**: Aggressive polling (10-15s) for real-time feel
- **Cellular**: Conservative polling (20-30s) to preserve data
- **Poor Signal**: Exponential backoff to prevent battery drain

### Backend Optimizations

**Planned Server Enhancements:**
1. **WebSocket Fallback**: For truly real-time critical events
2. **Delta Updates**: Only send changed data fields
3. **Push Notifications**: For urgent alerts (high heart rate, location changes)
4. **Batch APIs**: Multiple data points in single request

### Testing Strategy

**Polling Test Coverage:**
```dart
// Widget test verification
testWidgets('stops polling after dispose', (tester) async {
  // Pump widget with fake API service
  // Navigate away from dashboard
  // Verify no additional API calls after disposal
});
```

**Performance Monitoring:**
- **API Call Frequency**: Track actual vs. expected poll intervals
- **Battery Impact**: Monitor battery drain in production
- **Network Usage**: Measure data consumption patterns
- **Error Rates**: Track failed requests and recovery times

### Migration Roadmap

**Phase 1** (Current): Basic 15s polling with auto-dispose
**Phase 2**: Dynamic intervals based on battery/network
**Phase 3**: ETag support for bandwidth optimization  
**Phase 4**: WebSocket integration for instant updates
**Phase 5**: ML-based adaptive polling based on pet behavior patterns

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

### Makefile Highlights

| Target | Purpose |
|--------|---------|
| `bootstrap` | Create venv, install deps, setup hooks & Flutter deps |
| `py.lint` | Ruff + Black check + mypy |
| `py.test` | Python tests only |
| `flutter.analyze` | Flutter analyzer |
| `flutter.test` | Flutter widget/unit tests |
| `security` | Bandit, safety, secrets scan, pip-audit |
| `test` | Full Python + Flutter test suite |
| `build` | Python package, SAM, debug APK |
| `deploy-*` | Environment deployments (dev/staging/prod w/ guard) |
| `simulate` | Local SAM API + telemetry simulator |

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
\n## Roadmap 🗺️

**Mobile UI & Experience:**
* [x] Glassmorphism design system with Material 3 integration
* [x] Adaptive polling with auto-dispose lifecycle management
* [ ] Dynamic glass design tokens (dark mode, blur intensity)
* [ ] ETag-based cache optimization for polling
* [ ] Battery-aware polling intervals
* [ ] WebSocket fallback for real-time critical events

**Platform & Infrastructure:**
* [ ] Real JWT / OIDC auth integration
* [ ] SBOM + provenance (SLSA level goals)
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

Security / crypto / auth components include placeholder implementations and must be replaced or hardened before production deployment. In other words: **do not throw this into production without putting it through obedience training**.

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

