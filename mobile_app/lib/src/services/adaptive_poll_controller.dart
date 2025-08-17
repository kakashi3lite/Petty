import 'dart:async';
import 'dart:math';

/// Controller for adaptive polling with dynamic intervals, jitter, and backoff
class AdaptivePollController {
  static const Duration _baseInterval = Duration(seconds: 12);
  static const Duration _maxInterval = Duration(minutes: 5);
  static const Duration _minInterval = Duration(seconds: 8);
  static const double _backoffMultiplier = 1.5;
  static const double _jitterFactor = 0.2;
  
  final Random _random = Random();
  Duration _currentInterval = _baseInterval;
  int _consecutiveErrors = 0;
  bool _isBackgroundMode = false;
  
  Timer? _timer;
  StreamController<void>? _controller;
  
  /// Creates a stream that emits ticks for polling
  Stream<void> get stream {
    _controller ??= StreamController<void>.broadcast();
    return _controller!.stream;
  }
  
  /// Start the adaptive polling
  void start() {
    stop(); // Ensure we don't have multiple timers
    _scheduleNext();
  }
  
  /// Stop the polling
  void stop() {
    _timer?.cancel();
    _timer = null;
  }
  
  /// Dispose resources
  void dispose() {
    stop();
    _controller?.close();
    _controller = null;
  }
  
  /// Call when a request succeeds - resets backoff
  void onRequestSuccess() {
    _consecutiveErrors = 0;
    _currentInterval = _isBackgroundMode 
        ? Duration(seconds: _baseInterval.inSeconds * 2)
        : _baseInterval;
  }
  
  /// Call when a request fails - applies backoff
  void onRequestFailure() {
    _consecutiveErrors++;
    final backoffSeconds = (_baseInterval.inSeconds * 
        pow(_backoffMultiplier, _consecutiveErrors.clamp(0, 4))).round();
    _currentInterval = Duration(seconds: backoffSeconds.clamp(
      _minInterval.inSeconds, 
      _maxInterval.inSeconds
    ));
  }
  
  /// Set background mode (longer intervals to save battery)
  void setBackgroundMode(bool isBackground) {
    _isBackgroundMode = isBackground;
    if (isBackground) {
      _currentInterval = Duration(seconds: _currentInterval.inSeconds * 2);
    } else {
      _currentInterval = _baseInterval;
    }
  }
  
  /// Get current interval for testing/debugging
  Duration get currentInterval => _currentInterval;
  
  /// Get current error count for testing/debugging  
  int get consecutiveErrors => _consecutiveErrors;
  
  void _scheduleNext() {
    if (_controller?.isClosed == true) return;
    
    final jitterMs = (_currentInterval.inMilliseconds * _jitterFactor * 
        (_random.nextDouble() - 0.5)).round();
    final nextInterval = Duration(
      milliseconds: _currentInterval.inMilliseconds + jitterMs
    );
    
    _timer = Timer(nextInterval, () {
      if (_controller?.isClosed == false) {
        _controller!.add(null);
        _scheduleNext();
      }
    });
  }
}