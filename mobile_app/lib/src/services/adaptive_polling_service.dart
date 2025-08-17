import 'dart:async';
import 'dart:math';

/// Adaptive polling service that adjusts polling intervals based on conditions
/// and implements proper debounce mechanisms
class AdaptivePollingService<T> {
  static const Duration _minInterval = Duration(seconds: 5);
  static const Duration _maxInterval = Duration(seconds: 60);
  static const Duration _defaultInterval = Duration(seconds: 15);
  static const Duration _debounceDelay = Duration(seconds: 2);
  
  Timer? _pollTimer;
  Timer? _debounceTimer;
  Duration _currentInterval = _defaultInterval;
  bool _isActive = false;
  int _consecutiveErrors = 0;
  DateTime? _lastSuccessfulPoll;
  
  // Callback function for polling
  Future<T> Function() _pollFunction;
  void Function(T data) _onData;
  void Function(Object error) _onError;
  
  AdaptivePollingService({
    required Future<T> Function() pollFunction,
    required void Function(T data) onData,
    required void Function(Object error) onError,
  }) : _pollFunction = pollFunction,
       _onData = onData,
       _onError = onError;

  /// Start adaptive polling
  void start() {
    if (_isActive) return;
    _isActive = true;
    _schedulePoll();
  }

  /// Stop polling and cleanup timers
  void stop() {
    _isActive = false;
    _pollTimer?.cancel();
    _debounceTimer?.cancel();
    _pollTimer = null;
    _debounceTimer = null;
  }

  /// Schedule the next poll with current interval
  void _schedulePoll() {
    if (!_isActive) return;
    
    _pollTimer?.cancel();
    _pollTimer = Timer(_currentInterval, _performPoll);
  }

  /// Perform the actual poll with debounce protection
  Future<void> _performPoll() async {
    if (!_isActive) return;

    // Cancel any pending debounced polls
    _debounceTimer?.cancel();
    
    try {
      final data = await _pollFunction();
      _onPollSuccess(data);
    } catch (error) {
      _onPollError(error);
    }
  }

  /// Handle successful poll
  void _onPollSuccess(T data) {
    _consecutiveErrors = 0;
    _lastSuccessfulPoll = DateTime.now();
    
    // Reset to default interval on success
    _adaptInterval(success: true);
    
    // Use debounce to prevent rapid updates
    _debounceTimer?.cancel();
    _debounceTimer = Timer(_debounceDelay, () {
      if (_isActive) {
        _onData(data);
      }
    });
    
    _schedulePoll();
  }

  /// Handle poll error with exponential backoff
  void _onPollError(Object error) {
    _consecutiveErrors++;
    
    // Adapt interval based on error count
    _adaptInterval(success: false);
    
    _onError(error);
    _schedulePoll();
  }

  /// Adapt polling interval based on success/failure patterns
  void _adaptInterval({required bool success}) {
    if (success) {
      // Gradually decrease interval on consistent success
      if (_consecutiveErrors == 0 && _currentInterval > _minInterval) {
        _currentInterval = Duration(
          milliseconds: max(
            _minInterval.inMilliseconds,
            (_currentInterval.inMilliseconds * 0.8).round(),
          ),
        );
      }
    } else {
      // Exponential backoff on errors
      _currentInterval = Duration(
        milliseconds: min(
          _maxInterval.inMilliseconds,
          (_currentInterval.inMilliseconds * pow(2, _consecutiveErrors)).round(),
        ),
      );
    }
  }

  /// Check if service is currently active
  bool get isActive => _isActive;
  
  /// Get current polling interval
  Duration get currentInterval => _currentInterval;
  
  /// Get number of consecutive errors
  int get consecutiveErrors => _consecutiveErrors;
  
  /// Get time of last successful poll
  DateTime? get lastSuccessfulPoll => _lastSuccessfulPoll;
}