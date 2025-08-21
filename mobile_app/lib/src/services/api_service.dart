import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:http/http.dart' as http;

/// Custom exceptions for better error handling
abstract class PettyException implements Exception {
  final String message;
  final int? statusCode;
  final String? details;

  const PettyException(this.message, this.statusCode, [this.details]);

  @override
  String toString() =>
      'PettyException: $message${details != null ? ' ($details)' : ''}';
}

class NetworkException extends PettyException {
  const NetworkException(String message, [int? statusCode, String? details])
      : super(message, statusCode, details);
}

class AuthenticationException extends PettyException {
  const AuthenticationException(String message, [String? details])
      : super(message, 401, details);
}

class ServerException extends PettyException {
  const ServerException(String message, int statusCode, [String? details])
      : super(message, statusCode, details);
}

class ValidationException extends PettyException {
  const ValidationException(String message, [String? details])
      : super(message, 400, details);
}

class TimeoutException extends PettyException {
  const TimeoutException(String message, [String? details])
      : super(message, 408, details);
}

/// Retry policy configuration
class RetryPolicy {
  final int maxAttempts;
  final Duration initialDelay;
  final double backoffMultiplier;
  final Duration maxDelay;
  final List<int> retryableStatusCodes;
  final List<Type> retryableExceptions;

  const RetryPolicy({
    this.maxAttempts = 3,
    this.initialDelay = const Duration(milliseconds: 500),
    this.backoffMultiplier = 2.0,
    this.maxDelay = const Duration(seconds: 30),
    this.retryableStatusCodes = const [429, 500, 502, 503, 504],
    this.retryableExceptions = const [
      SocketException,
      HttpException,
      TimeoutException,
      NetworkException,
    ],
  });

  /// Calculate delay for retry attempt with jitter
  Duration getRetryDelay(int attemptNumber) {
    final baseDelay =
        initialDelay.inMilliseconds * pow(backoffMultiplier, attemptNumber - 1);
    final jitter = Random().nextDouble() * 0.1; // Add 10% jitter
    final delayWithJitter = (baseDelay * (1 + jitter)).round();
    final clampedDelay = min(delayWithJitter, maxDelay.inMilliseconds);
    return Duration(milliseconds: clampedDelay);
  }

  /// Check if exception is retryable
  bool isRetryableException(Exception exception) {
    return retryableExceptions.any((type) => exception.runtimeType == type) ||
        (exception is PettyException &&
            exception.statusCode != null &&
            retryableStatusCodes.contains(exception.statusCode));
  }
}

/// Circuit breaker pattern implementation
class CircuitBreaker {
  final int failureThreshold;
  final Duration timeout;
  final Duration resetTimeout;

  int _failureCount = 0;
  DateTime? _lastFailureTime;
  bool _isOpen = false;

  CircuitBreaker({
    this.failureThreshold = 5,
    this.timeout = const Duration(seconds: 60),
    this.resetTimeout = const Duration(seconds: 30),
  });

  bool get isOpen => _isOpen;
  bool get isHalfOpen =>
      _isOpen &&
      _lastFailureTime != null &&
      DateTime.now().difference(_lastFailureTime!) > resetTimeout;

  void recordSuccess() {
    _failureCount = 0;
    _isOpen = false;
    _lastFailureTime = null;
  }

  void recordFailure() {
    _failureCount++;
    _lastFailureTime = DateTime.now();

    if (_failureCount >= failureThreshold) {
      _isOpen = true;
    }
  }

  Future<T> execute<T>(Future<T> Function() operation) async {
    if (isOpen && !isHalfOpen) {
      throw const ServerException(
          'Circuit breaker is open - service temporarily unavailable', 503);
    }

    try {
      final result = await operation();
      recordSuccess();
      return result;
    } catch (e) {
      recordFailure();
      rethrow;
    }
  }
}

/// Production-grade API service with comprehensive error handling
class APIService {
  APIService({
    required this.baseUrl,
    this.apiVersion = 'v1',
    this.timeout = const Duration(seconds: 30),
    RetryPolicy? retryPolicy,
  })  : _retryPolicy = retryPolicy ?? const RetryPolicy(),
        _circuitBreaker = CircuitBreaker();

  final String baseUrl;
  final String apiVersion;
  final Duration timeout;
  final RetryPolicy _retryPolicy;
  final CircuitBreaker _circuitBreaker;

  late final http.Client _httpClient = http.Client();

  String get _baseApiUrl => '$baseUrl/$apiVersion';

  /// Execute HTTP request with retry logic and circuit breaker
  Future<T> _executeWithRetry<T>(
    String operation,
    Future<T> Function() request,
  ) async {
    Exception? lastException;

    for (int attempt = 1; attempt <= _retryPolicy.maxAttempts; attempt++) {
      try {
        return await _circuitBreaker.execute(request);
      } catch (e) {
        lastException = e is Exception ? e : Exception(e.toString());

        // Don't retry on last attempt or non-retryable exceptions
        if (attempt == _retryPolicy.maxAttempts ||
            !_retryPolicy.isRetryableException(lastException)) {
          break;
        }

        // Wait before retry with exponential backoff
        final delay = _retryPolicy.getRetryDelay(attempt);
        print(
            '[$operation] Attempt $attempt failed, retrying in ${delay.inMilliseconds}ms: ${e.toString()}');
        await Future.delayed(delay);
      }
    }

    throw lastException ?? const NetworkException('Unknown error occurred');
  }

  /// Convert HTTP response to appropriate exception
  PettyException _handleHttpError(http.Response response, String operation) {
    final statusCode = response.statusCode;
    final body = response.body.isNotEmpty ? response.body : 'No response body';

    switch (statusCode) {
      case 400:
        return ValidationException('Invalid request for $operation', body);
      case 401:
        return AuthenticationException(
            'Authentication failed for $operation', body);
      case 403:
        return AuthenticationException('Access forbidden for $operation', body);
      case 404:
        return ValidationException('Resource not found for $operation', body);
      case 408:
        return TimeoutException('Request timeout for $operation', body);
      case 429:
        return NetworkException(
            'Rate limit exceeded for $operation', statusCode, body);
      case >= 500:
        return ServerException(
            'Server error during $operation', statusCode, body);
      default:
        return NetworkException(
            'HTTP error during $operation', statusCode, body);
    }
  }

  /// Execute HTTP GET request with error handling
  Future<Map<String, dynamic>> _get(String endpoint,
      {Map<String, String>? queryParams}) async {
    return _executeWithRetry('GET $endpoint', () async {
      try {
        final uri = Uri.parse('$_baseApiUrl/$endpoint')
            .replace(queryParameters: queryParams);

        final response = await _httpClient.get(
          uri,
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'PettyApp/1.0',
            'Accept': 'application/json',
          },
        ).timeout(timeout);

        if (response.statusCode >= 400) {
          throw _handleHttpError(response, 'GET $endpoint');
        }

        final decoded = json.decode(response.body);
        if (decoded is! Map<String, dynamic>) {
          throw ValidationException('Invalid response format from $endpoint');
        }

        return decoded;
      } on SocketException catch (e) {
        throw NetworkException(
            'Network error during GET $endpoint', null, e.message);
      } on FormatException catch (e) {
        throw ValidationException(
            'Invalid JSON response from $endpoint', e.message);
      } on http.ClientException catch (e) {
        throw NetworkException(
            'HTTP client error during GET $endpoint', null, e.message);
      }
    });
  }

  /// Execute HTTP POST request with error handling
  Future<Map<String, dynamic>> _post(
      String endpoint, Map<String, dynamic> data) async {
    return _executeWithRetry('POST $endpoint', () async {
      try {
        final uri = Uri.parse('$_baseApiUrl/$endpoint');

        final response = await _httpClient
            .post(
              uri,
              headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'PettyApp/1.0',
                'Accept': 'application/json',
              },
              body: json.encode(data),
            )
            .timeout(timeout);

        if (response.statusCode >= 400) {
          throw _handleHttpError(response, 'POST $endpoint');
        }

        if (response.body.isEmpty) {
          return <String, dynamic>{}; // Success with no body
        }

        final decoded = json.decode(response.body);
        if (decoded is! Map<String, dynamic>) {
          throw ValidationException('Invalid response format from $endpoint');
        }

        return decoded;
      } on SocketException catch (e) {
        throw NetworkException(
            'Network error during POST $endpoint', null, e.message);
      } on FormatException catch (e) {
        throw ValidationException(
            'Invalid JSON response from $endpoint', e.message);
      } on http.ClientException catch (e) {
        throw NetworkException(
            'HTTP client error during POST $endpoint', null, e.message);
      }
    });
  }

  /// Get real-time data for a collar
  Future<Map<String, dynamic>> getRealTimeData(String collarId) async {
    if (collarId.isEmpty) {
      throw const ValidationException('Collar ID cannot be empty');
    }

    return _get('realtime', queryParams: {'collar_id': collarId});
  }

  /// Get pet plan for a collar
  Future<Map<String, dynamic>> getPetPlan(String collarId) async {
    if (collarId.isEmpty) {
      throw const ValidationException('Collar ID cannot be empty');
    }

    return _get('pet-plan', queryParams: {'collar_id': collarId});
  }

  /// Get pet timeline for a collar
  Future<List<dynamic>> getPetTimeline(String collarId) async {
    if (collarId.isEmpty) {
      throw const ValidationException('Collar ID cannot be empty');
    }

    final response =
        await _get('pet-timeline', queryParams: {'collar_id': collarId});
    final timeline = response['timeline'];

    if (timeline is! List) {
      throw ValidationException('Invalid timeline format in response');
    }

    return timeline;
  }

  /// Submit user feedback for an event
  Future<void> submitFeedback(String eventId, String feedback) async {
    if (eventId.isEmpty) {
      throw const ValidationException('Event ID cannot be empty');
    }
    if (feedback.isEmpty) {
      throw const ValidationException('Feedback cannot be empty');
    }
    if (feedback.length > 1000) {
      throw const ValidationException(
          'Feedback too long (max 1000 characters)');
    }

    await _post('submit-feedback', {
      'event_id': eventId,
      'user_feedback': feedback,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// Get circuit breaker status for monitoring
  Map<String, dynamic> getCircuitBreakerStatus() {
    return {
      'isOpen': _circuitBreaker.isOpen,
      'isHalfOpen': _circuitBreaker.isHalfOpen,
      'failureCount': _circuitBreaker._failureCount,
      'lastFailureTime': _circuitBreaker._lastFailureTime?.toIso8601String(),
    };
  }

  /// Close HTTP client and clean up resources
  void dispose() {
    _httpClient.close();
  }
}
