import 'dart:convert';
import 'package:http/http.dart' as http;
import 'cache_service.dart';

class APIService {
  APIService({required this.baseUrl}) {
    _cache.initialize();
  }
  
  final String baseUrl;
  final CacheService _cache = CacheService();

  Future<Map<String, dynamic>> getRealTimeData(String collarId) async {
    final cacheKey = CacheKeys.realTimeDataForCollar(collarId);
    
    // Try cache first
    final cachedData = _cache.get<Map<String, dynamic>>(cacheKey);
    if (cachedData != null) {
      return cachedData;
    }
    
    // Fetch from API
    final r = await http.get(Uri.parse('$baseUrl/realtime?collar_id=$collarId'));
    if (r.statusCode >= 400) throw Exception('Realtime error: ${r.statusCode}');
    
    final data = json.decode(r.body) as Map<String, dynamic>;
    
    // Cache with short TTL for real-time data
    _cache.set(cacheKey, data, ttl: const Duration(seconds: 30));
    
    return data;
  }

  Future<Map<String, dynamic>> getPetPlan(String collarId) async {
    final cacheKey = CacheKeys.planForCollar(collarId);
    
    // Try cache first
    final cachedData = _cache.get<Map<String, dynamic>>(cacheKey);
    if (cachedData != null) {
      return cachedData;
    }
    
    final r = await http.get(Uri.parse('$baseUrl/pet-plan?collar_id=$collarId'));
    if (r.statusCode >= 400) throw Exception('Plan error: ${r.statusCode}');
    
    final data = json.decode(r.body) as Map<String, dynamic>;
    
    // Cache with longer TTL for plan data
    _cache.set(cacheKey, data, ttl: const Duration(hours: 1));
    
    return data;
  }

  Future<List<dynamic>> getPetTimeline(String collarId) async {
    final cacheKey = CacheKeys.timelineForCollar(collarId);
    
    // Try cache first
    final cachedData = _cache.get<List<dynamic>>(cacheKey);
    if (cachedData != null) {
      return cachedData;
    }
    
    final r = await http.get(Uri.parse('$baseUrl/pet-timeline?collar_id=$collarId'));
    if (r.statusCode >= 400) throw Exception('Timeline error: ${r.statusCode}');
    final decoded = json.decode(r.body) as Map<String, dynamic>;
    final timeline = (decoded['timeline'] as List<dynamic>? ?? <dynamic>[]);
    
    // Cache with medium TTL for timeline data
    _cache.set(cacheKey, timeline, ttl: const Duration(minutes: 15));
    
    return timeline;
  }

  Future<void> submitFeedback(String eventId, String feedback) async {
    final r = await http.post(Uri.parse('$baseUrl/submit-feedback'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({"event_id": eventId, "user_feedback": feedback}));
    if (r.statusCode >= 400) throw Exception('Feedback error: ${r.statusCode} ${r.body}');
  }
}
