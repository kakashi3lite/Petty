# Mobile UI Theming & Adaptive Polling (Extended Design)

This document restores the deep-dive material that was intentionally trimmed from the minimalist `README.md`. The README stays lean; this file carries the richer rationale, patterns, and implementation notes.

## Goals

1. Provide a polished, brandable Flutter Material 3 experience with subtle glassmorphism accents.
2. Keep performance smooth (60fps target) on mid‑range devices.
3. Implement *adaptive* telemetry polling (dynamic interval + backoff) instead of a fixed cadence.
4. Preserve battery life and data quota by avoiding redundant network calls.
5. Maintain accessibility (contrast, scalable text, screen reader semantics).

## Design Pillars

| Pillar | Practical Translation |
|--------|-----------------------|
| Clarity | High contrast surfaces, motion reduced for users with preferences. |
| Calm Feedback | Non-blocking toasts/snackbars; animated subtle blurs only when visible. |
| Intentional Motion | Use implicit animations (AnimatedOpacity / AnimatedContainer) and short (120–160ms) cubic curves. |
| Battery Aware | Poll less when user idle or backgrounded. |
| Resilient Offline | Local queue + optimistic UI; retry with jitter. |

## Color & Surface System

We keep Material 3 dynamic color compatibility while allowing a brand override.

```dart
// Brand seed color (fallback if dynamic colors unsupported)
const brandSeed = Color(0xFF6750A4); // Example purple

ColorScheme buildColorScheme(Brightness brightness, Color? dynamicSeed) {
  final seed = dynamicSeed ?? brandSeed;
  return ColorScheme.fromSeed(seedColor: seed, brightness: brightness);
}
```

### Elevation + Glass Layer

We simulate glass by composing:
1. Slight blur (BackdropFilter sigma 10–14)
2. Semi-transparent fill (ColorScheme.surface.withOpacity(0.55))
3. 1px subtle white overlay highlight at top edge (gradient) for depth
4. Border using surfaceVariant with 30% opacity

```dart
class GlassPanel extends StatelessWidget {
  final Widget child;
  final double radius;
  const GlassPanel({super.key, required this.child, this.radius = 18});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: DecoratedBox(
          decoration: BoxDecoration(
            border: Border.all(color: scheme.surfaceVariant.withOpacity(.3)),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                scheme.surface.withOpacity(.55),
                scheme.surface.withOpacity(.35),
              ],
            ),
          ),
          child: child,
        ),
      ),
    );
  }
}
```

Performance note: Only apply BackdropFilter on limited areas (panels, headers) not full screen; avoid stacking multiple overlapping filters.

## Typography & Scaling

Use Material 3 text themes but respect user text scale. Ensure no hard-coded font sizes inside custom widgets; rely on `Theme.of(context).textTheme`. Where truncation risk exists, allow wrapping or provide flexible layout.


## State Management

We continue with Riverpod (as implied by existing patterns) for:

- Telemetry stream provider
- Adaptive polling controller provider
- Theme/dynamic color provider

Advantages: testability, fine-grained rebuilds, DI friendliness.

## Adaptive Polling Strategy

### Motivation

Static 15s polling wastes bandwidth when no changes occur and can feel sluggish when recent activity spikes.

### Interval Model

| Condition | Target Interval |
|-----------|-----------------|
| Fresh user interaction (last 30s) | 5s |
| Recent activity events detected | 5–8s (fast lane) |
| Idle 2–5 min | 20s |
| Idle >5 min (app foreground) | 30–45s (linear backoff) |
| App background (resumable) | Suspend or >60s (OS permitting) |
| Error burst (>=3 failures) | Exponential backoff: 10s, 20s, 40s, cap 60s |

### Algorithm (High Level)

1. On each cycle, evaluate context metrics:
   - `lastUserInteraction` delta
   - `recentEventTimestamps` window density
   - Failure count & last status
   - App lifecycle state (foreground/background)
2. Choose base interval from interaction/activity heuristics.
3. Apply error backoff multiplier if recent consecutive failures.
4. Apply jitter (+/- 10%) to prevent thundering herd.
5. Schedule next fetch unless lifecycle suspended.

### Pseudocode

```dart
class AdaptivePollController {
  Duration baseFast = const Duration(seconds: 5);
  Duration baseNormal = const Duration(seconds: 15);
  Duration baseIdle = const Duration(seconds: 30);
  Duration maxBackoff = const Duration(seconds: 60);

  int failureStreak = 0;
  DateTime lastInteraction = DateTime.now();
  final List<DateTime> recentEvents = [];

  Duration computeNext() {
    final now = DateTime.now();
    final idleSeconds = now.difference(lastInteraction).inSeconds;
    Duration candidate;
    final activityDensity = recentEvents.where((e) => now.difference(e).inSeconds < 45).length;

    if (idleSeconds < 30 || activityDensity > 3) {
      candidate = baseFast; // high engagement
    } else if (idleSeconds < 300) {
      candidate = baseNormal; // typical
    } else {
      // extended idle grows toward baseIdle * 1.5
      final factor = (idleSeconds / 300).clamp(1, 1.5);
      candidate = Duration(milliseconds: (baseIdle.inMilliseconds * factor).round());
    }

    if (failureStreak > 0) {
      final backoff = Duration(seconds: (5 * (1 << (failureStreak - 1))).clamp(5, maxBackoff.inSeconds));
      candidate = backoff > candidate ? backoff : candidate;
    }

    // Jitter ±10%
    final jitterFactor = (1 + (Random().nextDouble() * 0.2 - 0.1));
    candidate = Duration(milliseconds: (candidate.inMilliseconds * jitterFactor).round());
    return candidate;
  }
}
```

### Failure Handling

- Reset `failureStreak` on success.
- Circuit-break after N (configurable) failures: surface offline banner, switch to exponential schedule until a success.

### Telemetry Stream Hook

Wrap `Stream.periodic` replacement with a controller that manually schedules the next fetch after each completion (success or failure), using `Timer` with the computed delay.

## Accessibility Considerations

- Blur surfaces still need contrast: test underlying text contrast with simulated opaque equivalent.
- Provide semantic labels for dynamic telemetry values; prefer `Semantics` widget.
- Respect reduced motion: if user opts out, disable blur and animated opacity transitions (fallback to solid surfaces).

## Testing Strategy

| Layer | Tests |
|-------|-------|
| Interval logic | Deterministic unit tests feeding synthetic timestamps & failure counts. |
| Widget (GlassPanel) | Golden tests (light/dark), semantics tests. |
| Stream integration | Fake repository returning synthetic event bursts; assert interval shrink/expand. |
| Performance | Profile build/rebuild counts with and without blur surfaces. |

## Performance Tips

- Avoid rebuilding BackdropFilter parents unnecessarily (use const constructors, keys, or split widgets).
- Cap stored `recentEvents` list (e.g., purge entries older than 2 minutes).
- Debounce interaction updates to at most 1 per 500ms.

## Configuration Surface

Expose a `PollingConfig` (immutable) for tuning.

```dart
class PollingConfig {
  final Duration fast;
  final Duration normal;
  final Duration idle;
  final Duration maxBackoff;
  final double jitterPercent; // 0.1 = ±10%
  const PollingConfig({
    this.fast = const Duration(seconds: 5),
    this.normal = const Duration(seconds: 15),
    this.idle = const Duration(seconds: 30),
    this.maxBackoff = const Duration(seconds: 60),
    this.jitterPercent = 0.10,
  });
}
```

Provider example:

```dart
final pollingConfigProvider = Provider<PollingConfig>((_) => const PollingConfig());
```

## Future Enhancements

- ML-derived cadence based on historical variance in telemetry.
- Push/stream (WebSocket or gRPC) fallback to polling only when streaming unavailable.
- Energy impact measurement hooks (Android BatteryStats integration).

## Migration Notes

1. Keep README minimal; link to this file if needed.
2. Introduce the adaptive controller in a separate PR to minimize risk.
3. Monitor error rate & average interval post-deployment.

---
Restored doc version: v1.0 (first extraction from expanded README history).
