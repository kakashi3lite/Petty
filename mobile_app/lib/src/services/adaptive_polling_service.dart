import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

/// Adaptive polling service with ETag support, exponential backoff, and jitter
class AdaptivePollingService {
  final String baseUrl;
  final Duration baseInterval;
  final Duration maxInterval;
  final int maxRetries;
  final Random _random = Random();
  
  // ETag cache for conditional requests
  final Map<String, String> _eTagCache = {};
  
  // Backoff state
  int _consecutiveErrors = 0;
  DateTime? _lastPollTime;
  
  AdaptivePollingService({
    required this.baseUrl,
    this.baseInterval = const Duration(seconds: 15),
    this.maxInterval = const Duration(minutes: 5),
    this.maxRetries = 3,
  });
  
  /// Calculate next poll interval with exponential backoff and jitter
  Duration _calculateNextInterval() {
    if (_consecutiveErrors == 0) {
      return baseInterval;
    }
    
    // Exponential backoff: 2^errors * baseInterval
    final backoffMultiplier = pow(2, _consecutiveErrors).clamp(1, 16).toInt();
    var interval = Duration(
      milliseconds: baseInterval.inMilliseconds * backoffMultiplier,
    );
    
    // Cap at max interval
    if (interval > maxInterval) {
      interval = maxInterval;
    }
    
    // Add jitter (±25%)
    final jitter = interval.inMilliseconds * 0.25;
    final jitterMs = (_random.nextDouble() - 0.5) * 2 * jitter;
    interval = Duration(
      milliseconds: (interval.inMilliseconds + jitterMs).round(),
    );
    
    return interval;
  }
  
  /// Make HTTP request with ETag support
  Future<http.Response> _makeRequest(String endpoint) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final headers = <String, String>{
      'Accept': 'application/json',
    };
    
    // Add If-None-Match header if we have ETag for this endpoint
    if (_eTagCache.containsKey(endpoint)) {
      headers['If-None-Match'] = _eTagCache[endpoint]!;
    }
    
    return await http.get(uri, headers: headers);
  }
  
  /// Handle response and update ETag cache
  Map<String, dynamic>? _handleResponse(
    http.Response response,
    String endpoint,
  ) {
    // Update ETag cache if present
    final etag = response.headers['etag'];
    if (etag != null) {
      _eTagCache[endpoint] = etag;
    }
    
    if (response.statusCode == 304) {
      // Not Modified - data hasn't changed
      return null;
    }
    
    if (response.statusCode >= 200 && response.statusCode < 300) {
      _consecutiveErrors = 0;
      try {
        return {'data': response.body, 'timestamp': DateTime.now().toIso8601String()};
      } catch (e) {
        throw FormatException('Invalid JSON response: $e');
      }
    }
    
    throw HttpException('HTTP ${response.statusCode}: ${response.body}');
  }
  
  /// Create adaptive polling stream
  Stream<Map<String, dynamic>> createPollingStream(String endpoint) async* {
    while (true) {
      try {
        // Respect debounce timing
        if (_lastPollTime != null) {
          final timeSinceLastPoll = DateTime.now().difference(_lastPollTime!);
          final nextInterval = _calculateNextInterval();
          
          if (timeSinceLastPoll < nextInterval) {
            await Future.delayed(nextInterval - timeSinceLastPoll);
          }
        }
        
        _lastPollTime = DateTime.now();
        
        final response = await _makeRequest(endpoint);
        final result = _handleResponse(response, endpoint);
        
        if (result != null) {
          yield result;
        }
        // If result is null (304 Not Modified), don't yield anything
        
      } catch (e) {
        _consecutiveErrors++;
        
        if (kDebugMode) {
          print('Polling error for $endpoint: $e');
        }
        
        // Yield error state but continue polling with backoff
        yield {
          'error': e.toString(),
          'timestamp': DateTime.now().toIso8601String(),
          'retryIn': _calculateNextInterval().inSeconds,
        };
        
        // Don't exceed max retries in quick succession
        if (_consecutiveErrors >= maxRetries) {
          await Future.delayed(_calculateNextInterval());
        }
      }
      
      // Base polling interval (will be adjusted by backoff logic above)
      await Future.delayed(const Duration(milliseconds: 100));
    }
  }
  
  /// Reset error state (useful when network conditions improve)
  void reset() {
    _consecutiveErrors = 0;
    _lastPollTime = null;
  }
  
  /// Clear ETag cache (useful for forced refresh)
  void clearCache() {
    _eTagCache.clear();
  }
}