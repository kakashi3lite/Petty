import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';

/// Offline cache service for storing API responses and app data
class OfflineCacheService {
  static const String _keyPrefix = 'petty_cache_';
  static const String _timestampSuffix = '_timestamp';
  
  static SharedPreferences? _prefs;
  
  /// Initialize the cache service
  static Future<void> initialize() async {
    _prefs ??= await SharedPreferences.getInstance();
  }
  
  /// Store data with automatic timestamp
  static Future<bool> store(String key, Map<String, dynamic> data) async {
    await initialize();
    
    final cacheKey = '$_keyPrefix$key';
    final timestampKey = '$cacheKey$_timestampSuffix';
    
    try {
      final success = await _prefs!.setString(cacheKey, jsonEncode(data));
      if (success) {
        await _prefs!.setInt(timestampKey, DateTime.now().millisecondsSinceEpoch);
      }
      return success;
    } catch (e) {
      if (kDebugMode) {
        print('Cache store error for $key: $e');
      }
      return false;
    }
  }
  
  /// Retrieve cached data with age check
  static Future<Map<String, dynamic>?> retrieve(
    String key, {
    Duration? maxAge,
  }) async {
    await initialize();
    
    final cacheKey = '$_keyPrefix$key';
    final timestampKey = '$cacheKey$_timestampSuffix';
    
    try {
      final dataStr = _prefs!.getString(cacheKey);
      if (dataStr == null) return null;
      
      // Check age if maxAge is specified
      if (maxAge != null) {
        final timestamp = _prefs!.getInt(timestampKey);
        if (timestamp == null) return null;
        
        final age = DateTime.now().millisecondsSinceEpoch - timestamp;
        if (age > maxAge.inMilliseconds) {
          // Cache expired, remove it
          await remove(key);
          return null;
        }
      }
      
      return jsonDecode(dataStr) as Map<String, dynamic>;
    } catch (e) {
      if (kDebugMode) {
        print('Cache retrieve error for $key: $e');
      }
      // Remove corrupted cache entry
      await remove(key);
      return null;
    }
  }
  
  /// Remove cached data
  static Future<bool> remove(String key) async {
    await initialize();
    
    final cacheKey = '$_keyPrefix$key';
    final timestampKey = '$cacheKey$_timestampSuffix';
    
    try {
      final success1 = await _prefs!.remove(cacheKey);
      final success2 = await _prefs!.remove(timestampKey);
      return success1 && success2;
    } catch (e) {
      if (kDebugMode) {
        print('Cache remove error for $key: $e');
      }
      return false;
    }
  }
  
  /// Clear all cache
  static Future<bool> clearAll() async {
    await initialize();
    
    try {
      final keys = _prefs!.getKeys().where((key) => key.startsWith(_keyPrefix));
      for (final key in keys) {
        await _prefs!.remove(key);
      }
      return true;
    } catch (e) {
      if (kDebugMode) {
        print('Cache clear all error: $e');
      }
      return false;
    }
  }
  
  /// Get cache info (for debugging)
  static Future<Map<String, dynamic>> getCacheInfo() async {
    await initialize();
    
    final keys = _prefs!.getKeys().where((key) => key.startsWith(_keyPrefix));
    final info = <String, dynamic>{};
    
    for (final key in keys) {
      if (!key.endsWith(_timestampSuffix)) {
        final timestamp = _prefs!.getInt('$key$_timestampSuffix');
        final size = _prefs!.getString(key)?.length ?? 0;
        
        info[key.substring(_keyPrefix.length)] = {
          'size_bytes': size,
          'timestamp': timestamp,
          'age_minutes': timestamp != null 
            ? (DateTime.now().millisecondsSinceEpoch - timestamp) / 60000
            : null,
        };
      }
    }
    
    return info;
  }
}

/// Cache keys for different data types
class CacheKeys {
  static const String realTimeData = 'realtime_data';
  static const String petTimeline = 'pet_timeline';
  static const String petPlan = 'pet_plan';
  static const String userPreferences = 'user_preferences';
  static const String appConfig = 'app_config';
}