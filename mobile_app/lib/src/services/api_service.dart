import 'dart:convert';
import 'package:http/http.dart' as http;

class APIService {
  APIService({required this.baseUrl});
  final String baseUrl;

  Future<Map<String, dynamic>> getRealTimeData(String collarId, {String? etag}) async {
    final headers = <String, String>{'Accept': 'application/json'};
    if (etag != null) {
      headers['If-None-Match'] = etag;
    }
    
    final r = await http.get(
      Uri.parse('$baseUrl/realtime?collar_id=$collarId'),
      headers: headers,
    );
    
    if (r.statusCode == 304) {
      // Not Modified - return special indicator
      return {'__not_modified': true, '__etag': etag};
    }
    
    if (r.statusCode >= 400) throw Exception('Realtime error: ${r.statusCode}');
    
    final data = json.decode(r.body) as Map<String, dynamic>;
    
    // Include ETag in response if present
    final responseEtag = r.headers['etag'];
    if (responseEtag != null) {
      data['__etag'] = responseEtag;
    }
    
    return data;
  }

  Future<Map<String, dynamic>> getPetPlan(String collarId) async {
    final r = await http.get(Uri.parse('$baseUrl/pet-plan?collar_id=$collarId'));
    if (r.statusCode >= 400) throw Exception('Plan error: ${r.statusCode}');
    return json.decode(r.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getPetTimeline(String collarId) async {
    final r = await http.get(Uri.parse('$baseUrl/pet-timeline?collar_id=$collarId'));
    if (r.statusCode >= 400) throw Exception('Timeline error: ${r.statusCode}');
    final decoded = json.decode(r.body) as Map<String, dynamic>;
    return (decoded['timeline'] as List<dynamic>? ?? <dynamic>[]);
  }

  Future<void> submitFeedback(String eventId, String feedback) async {
    final r = await http.post(Uri.parse('$baseUrl/submit-feedback'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({"event_id": eventId, "user_feedback": feedback}));
    if (r.statusCode >= 400) throw Exception('Feedback error: ${r.statusCode} ${r.body}');
  }
}
