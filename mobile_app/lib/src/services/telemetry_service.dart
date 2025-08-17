import 'package:flutter/foundation.dart';
import 'package:sentry_flutter/sentry_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Telemetry service for opt-in analytics and crash reporting
class TelemetryService {
  static const String _consentKey = 'telemetry_consent';
  static const String _sentryDsn = 'YOUR_SENTRY_DSN_HERE'; // Replace with actual DSN
  
  static bool _isInitialized = false;
  static bool _hasConsent = false;
  
  /// Initialize telemetry service
  static Future<void> initialize() async {
    if (_isInitialized) return;
    
    final prefs = await SharedPreferences.getInstance();
    _hasConsent = prefs.getBool(_consentKey) ?? false;
    
    if (_hasConsent && !kDebugMode) {
      await SentryFlutter.init(
        (options) {
          options.dsn = _sentryDsn;
          options.tracesSampleRate = 0.1; // 10% of transactions
          options.environment = kReleaseMode ? 'production' : 'staging';
          options.beforeSend = (event, hint) {
            // Only send if user has given consent
            return _hasConsent ? event : null;
          };
        },
      );
    }
    
    _isInitialized = true;
  }
  
  /// Request user consent for telemetry
  static Future<bool> requestConsent() async {
    // This would typically show a dialog to the user
    // For now, return false to maintain privacy
    return false;
  }
  
  /// Set telemetry consent
  static Future<void> setConsent(bool consent) async {
    _hasConsent = consent;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_consentKey, consent);
    
    if (consent && !_isInitialized) {
      await initialize();
    }
  }
  
  /// Check if user has given consent
  static bool get hasConsent => _hasConsent;
  
  /// Log a custom event (only if consent given)
  static void logEvent(String name, {Map<String, dynamic>? parameters}) {
    if (!_hasConsent || !_isInitialized) return;
    
    Sentry.addBreadcrumb(Breadcrumb(
      message: name,
      data: parameters,
      category: 'user_action',
      level: SentryLevel.info,
    ));
  }
  
  /// Log performance metrics
  static void logPerformance(String operation, Duration duration) {
    if (!_hasConsent || !_isInitialized) return;
    
    Sentry.getSpan()?.setData('operation', operation);
    Sentry.getSpan()?.setData('duration_ms', duration.inMilliseconds);
  }
  
  /// Log an error (only if consent given)
  static void logError(dynamic error, {StackTrace? stackTrace, String? hint}) {
    if (!_hasConsent || !_isInitialized) return;
    
    Sentry.captureException(
      error,
      stackTrace: stackTrace,
      hint: hint != null ? Hint.withMap({'hint': hint}) : null,
    );
  }
  
  /// Track user flow/navigation
  static void trackScreen(String screenName) {
    if (!_hasConsent || !_isInitialized) return;
    
    Sentry.addBreadcrumb(Breadcrumb(
      message: 'Screen viewed: $screenName',
      category: 'navigation',
      level: SentryLevel.info,
    ));
  }
}

/// Remote configuration service for feature flags
class RemoteConfigService {
  static const Map<String, dynamic> _defaultConfig = {
    'enable_adaptive_polling': true,
    'polling_base_interval_seconds': 15,
    'polling_max_interval_seconds': 300,
    'cache_max_age_minutes': 60,
    'enable_glassmorphism': true,
    'performance_monitoring_enabled': true,
  };
  
  static Map<String, dynamic> _config = Map.from(_defaultConfig);
  
  /// Initialize remote config (placeholder for actual remote config service)
  static Future<void> initialize() async {
    // In a real app, this would fetch from Firebase Remote Config,
    // AWS AppConfig, or similar service
    
    // For now, load from local storage if available
    try {
      final prefs = await SharedPreferences.getInstance();
      final configJson = prefs.getString('remote_config');
      if (configJson != null) {
        // In a real implementation, you'd parse JSON here
        // _config = jsonDecode(configJson);
      }
    } catch (e) {
      // Use default config on error
      if (kDebugMode) {
        print('Failed to load remote config: $e');
      }
    }
  }
  
  /// Get a boolean configuration value
  static bool getBool(String key) {
    return _config[key] as bool? ?? false;
  }
  
  /// Get an integer configuration value
  static int getInt(String key) {
    return _config[key] as int? ?? 0;
  }
  
  /// Get a string configuration value
  static String getString(String key) {
    return _config[key] as String? ?? '';
  }
  
  /// Get a double configuration value
  static double getDouble(String key) {
    return (_config[key] as num?)?.toDouble() ?? 0.0;
  }
  
  /// Fetch latest config from remote source
  static Future<void> fetchAndActivate() async {
    // Placeholder for remote fetch
    // In a real app, this would fetch from remote service
    await Future.delayed(const Duration(milliseconds: 100));
  }
}