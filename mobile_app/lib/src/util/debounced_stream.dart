import 'dart:async';
import 'dart:math';

/// Configuration for adaptive polling behavior
class PollingConfig {
  final Duration fast;
  final Duration normal;
  final Duration idle;
  final Duration maxBackoff;
  final Duration minDebounce;
  final double jitterPercent;

  const PollingConfig({
    this.fast = const Duration(seconds: 5),
    this.normal = const Duration(seconds: 15),
    this.idle = const Duration(seconds: 30),
    this.maxBackoff = const Duration(seconds: 60),
    this.minDebounce = const Duration(seconds: 12),
    this.jitterPercent = 0.10,
  });
}

/// Adaptive polling controller that manages dynamic intervals
class AdaptivePollingController {
  final PollingConfig config;
  int failureStreak = 0;
  DateTime lastInteraction = DateTime.now();
  DateTime? lastDataChange;
  final List<DateTime> recentEvents = [];
  bool _isActive = true;

  AdaptivePollingController({this.config = const PollingConfig()});

  /// Update user interaction timestamp
  void recordUserInteraction() {
    lastInteraction = DateTime.now();
  }

  /// Record data change event
  void recordDataChange() {
    final now = DateTime.now();
    lastDataChange = now;
    recentEvents.add(now);
    // Keep only recent events (last 2 minutes)
    recentEvents.removeWhere((e) => now.difference(e).inSeconds > 120);
  }

  /// Set active state (app visibility)
  void setActive(bool active) {
    _isActive = active;
    if (active) {
      recordUserInteraction();
    }
  }

  /// Reset failure streak on success
  void recordSuccess() {
    failureStreak = 0;
  }

  /// Increment failure streak
  void recordFailure() {
    failureStreak++;
  }

  /// Compute next polling interval based on current state
  Duration computeNextInterval() {
    final now = DateTime.now();
    final idleSeconds = now.difference(lastInteraction).inSeconds;
    Duration candidate;

    // Check for recent data changes (within last minute)
    final hasRecentDataChange = lastDataChange != null && 
        now.difference(lastDataChange!).inSeconds < 60;

    // Calculate activity density (events in last 45 seconds)
    final activityDensity = recentEvents
        .where((e) => now.difference(e).inSeconds < 45)
        .length;

    // Determine base interval based on activity and app state
    if (!_isActive) {
      // App is backgrounded - use longer intervals
      candidate = config.idle;
    } else if ((idleSeconds < 30 && _isActive) || 
               activityDensity > 3 || 
               hasRecentDataChange) {
      // High engagement or recent activity
      candidate = config.fast;
    } else if (idleSeconds < 300) {
      // Typical usage
      candidate = config.normal;
    } else {
      // Extended idle - gradually increase interval
      final factor = (idleSeconds / 300).clamp(1.0, 1.5);
      candidate = Duration(
        milliseconds: (config.idle.inMilliseconds * factor).round()
      );
    }

    // Apply failure backoff
    if (failureStreak > 0) {
      final backoffMultiplier = min(1 << (failureStreak - 1), 8);
      final backoff = Duration(
        seconds: min(5 * backoffMultiplier, config.maxBackoff.inSeconds)
      );
      candidate = backoff > candidate ? backoff : candidate;
    }

    // Apply jitter to prevent thundering herd
    final jitterFactor = 1 + (Random().nextDouble() * 2 - 1) * config.jitterPercent;
    candidate = Duration(
      milliseconds: (candidate.inMilliseconds * jitterFactor).round()
    );

    // Ensure minimum debounce interval
    if (candidate < config.minDebounce) {
      candidate = config.minDebounce;
    }

    return candidate;
  }
}

/// Stream controller for adaptive polling with debounce and lifecycle management
class DebouncedAdaptiveStream<T> {
  final Future<T> Function() fetchFunction;
  final AdaptivePollingController controller;
  late final StreamController<T> _streamController;
  Timer? _timer;
  bool _isDisposed = false;

  DebouncedAdaptiveStream({
    required this.fetchFunction,
    AdaptivePollingController? controller,
  }) : controller = controller ?? AdaptivePollingController() {
    _streamController = StreamController<T>(
      onListen: _startPolling,
      onCancel: dispose,
    );
  }

  /// Get the stream
  Stream<T> get stream => _streamController.stream;

  /// Start the polling cycle
  void _startPolling() {
    if (_isDisposed) return;
    _scheduleNext();
  }

  /// Schedule the next fetch
  void _scheduleNext([Duration? customDelay]) {
    if (_isDisposed) return;
    
    _timer?.cancel();
    
    final delay = customDelay ?? controller.computeNextInterval();
    
    _timer = Timer(delay, () async {
      if (_isDisposed) return;
      
      try {
        final data = await fetchFunction();
        if (!_isDisposed) {
          controller.recordSuccess();
          controller.recordDataChange();
          _streamController.add(data);
          _scheduleNext();
        }
      } catch (error) {
        if (!_isDisposed) {
          controller.recordFailure();
          _streamController.addError(error);
          _scheduleNext();
        }
      }
    });
  }

  /// Record user interaction to influence polling rate
  void recordUserInteraction() {
    controller.recordUserInteraction();
  }

  /// Set app active state
  void setActive(bool active) {
    controller.setActive(active);
  }

  /// Dispose and clean up resources
  void dispose() {
    if (_isDisposed) return;
    _isDisposed = true;
    _timer?.cancel();
    _timer = null;
    if (!_streamController.isClosed) {
      _streamController.close();
    }
  }
}