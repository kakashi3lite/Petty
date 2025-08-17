import 'dart:convert';
import 'dart:async';

/// Simple in-memory cache service with TTL (Time To Live) support
/// for offline functionality and reducing API calls
class CacheService {
  static final CacheService _instance = CacheService._internal();
  factory CacheService() => _instance;
  CacheService._internal();

  final Map<String, _CacheEntry> _cache = {};
  Timer? _cleanupTimer;

  /// Default cache duration
  static const Duration defaultTTL = Duration(minutes: 5);

  /// Initialize cache service with periodic cleanup
  void initialize() {
    _startCleanupTimer();
  }

  /// Store data in cache with optional TTL
  void set<T>(String key, T data, {Duration? ttl}) {
    final expiry = DateTime.now().add(ttl ?? defaultTTL);
    _cache[key] = _CacheEntry(data, expiry);
  }

  /// Retrieve data from cache
  T? get<T>(String key) {
    final entry = _cache[key];
    if (entry == null) return null;
    
    if (entry.isExpired) {
      _cache.remove(key);
      return null;
    }
    
    return entry.data as T?;
  }

  /// Check if key exists and is not expired
  bool has(String key) {
    final entry = _cache[key];
    if (entry == null) return false;
    
    if (entry.isExpired) {
      _cache.remove(key);
      return false;
    }
    
    return true;
  }

  /// Remove specific key from cache
  void remove(String key) {
    _cache.remove(key);
  }

  /// Clear all cache entries
  void clear() {
    _cache.clear();
  }

  /// Get cache statistics
  CacheStats getStats() {
    final now = DateTime.now();
    int expired = 0;
    int active = 0;
    
    for (final entry in _cache.values) {
      if (entry.isExpired) {
        expired++;
      } else {
        active++;
      }
    }
    
    return CacheStats(
      totalEntries: _cache.length,
      activeEntries: active,
      expiredEntries: expired,
    );
  }

  /// Start periodic cleanup of expired entries
  void _startCleanupTimer() {
    _cleanupTimer?.cancel();
    _cleanupTimer = Timer.periodic(
      const Duration(minutes: 1),
      (_) => _cleanupExpired(),
    );
  }

  /// Remove expired entries
  void _cleanupExpired() {
    final keysToRemove = <String>[];
    
    for (final entry in _cache.entries) {
      if (entry.value.isExpired) {
        keysToRemove.add(entry.key);
      }
    }
    
    for (final key in keysToRemove) {
      _cache.remove(key);
    }
  }

  /// Dispose cache service
  void dispose() {
    _cleanupTimer?.cancel();
    _cache.clear();
  }
}

/// Cache entry with expiration time
class _CacheEntry {
  final dynamic data;
  final DateTime expiry;

  _CacheEntry(this.data, this.expiry);

  bool get isExpired => DateTime.now().isAfter(expiry);
}

/// Cache statistics
class CacheStats {
  final int totalEntries;
  final int activeEntries;
  final int expiredEntries;

  const CacheStats({
    required this.totalEntries,
    required this.activeEntries,
    required this.expiredEntries,
  });

  double get hitRatio => totalEntries > 0 ? activeEntries / totalEntries : 0.0;
}

/// Cache keys for consistent caching
class CacheKeys {
  static const String realTimeData = 'real_time_data';
  static const String petTimeline = 'pet_timeline';
  static const String petPlan = 'pet_plan';
  
  static String realTimeDataForCollar(String collarId) => '${realTimeData}_$collarId';
  static String timelineForCollar(String collarId) => '${petTimeline}_$collarId';
  static String planForCollar(String collarId) => '${petPlan}_$collarId';
}