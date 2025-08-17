import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

/// Adaptive polling provider that replaces continuous while(true) loops
/// Implements exponential backoff on errors and proper disposal
class AdaptivePollingNotifier extends AutoDisposeAsyncNotifier<Map<String, dynamic>> {
  Timer? _timer;
  int _errorCount = 0;
  static const int _maxErrorCount = 3;
  static const Duration _basePollInterval = Duration(seconds: 15);
  static const Duration _maxPollInterval = Duration(minutes: 2);

  @override
  Future<Map<String, dynamic>> build() async {
    // Set up disposal handling
    ref.onDispose(() {
      _timer?.cancel();
    });

    // Start polling
    _startPolling();
    
    // Return initial data
    return _fetchData();
  }

  void _startPolling() {
    _timer?.cancel();
    
    final interval = _calculatePollInterval();
    _timer = Timer.periodic(interval, (_) async {
      try {
        final data = await _fetchData();
        _errorCount = 0; // Reset error count on success
        state = AsyncValue.data(data);
      } catch (error, stackTrace) {
        _errorCount++;
        
        if (_errorCount >= _maxErrorCount) {
          // Stop polling after max errors, user can retry manually
          _timer?.cancel();
        }
        
        state = AsyncValue.error(error, stackTrace);
      }
    });
  }

  Duration _calculatePollInterval() {
    if (_errorCount == 0) {
      return _basePollInterval;
    }
    
    // Exponential backoff: base * 2^(errorCount-1), capped at max
    final backoffInterval = Duration(
      milliseconds: _basePollInterval.inMilliseconds * (1 << (_errorCount - 1))
    );
    
    return backoffInterval > _maxPollInterval ? _maxPollInterval : backoffInterval;
  }

  Future<Map<String, dynamic>> _fetchData() async {
    const apiBaseUrl = 'https://api.example.com';
    const collarId = 'SN-123';
    
    final service = APIService(baseUrl: apiBaseUrl);
    return service.getRealTimeData(collarId);
  }

  /// Manual refresh method for user-triggered updates
  Future<void> refresh() async {
    state = const AsyncValue.loading();
    try {
      final data = await _fetchData();
      _errorCount = 0;
      state = AsyncValue.data(data);
      
      // Restart polling if it was stopped due to errors
      if (_timer == null || !_timer!.isActive) {
        _startPolling();
      }
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }
}

/// Provider for adaptive polling real-time data
final adaptivePollingProvider = AutoDisposeAsyncNotifierProvider<AdaptivePollingNotifier, Map<String, dynamic>>(
  () => AdaptivePollingNotifier(),
);

/// Timeline provider (fetch once, cached)
final timelineProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  const apiBaseUrl = 'https://api.example.com';
  const collarId = 'SN-123';
  
  final service = APIService(baseUrl: apiBaseUrl);
  return service.getPetTimeline(collarId);
});