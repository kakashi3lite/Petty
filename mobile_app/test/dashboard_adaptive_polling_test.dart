import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';
import 'package:petty/src/providers/data_providers.dart';
import 'package:petty/src/services/api_service.dart';

void main() {
  group('Dashboard Screen Tests', () {
    testWidgets('Dashboard shows connection status indicator', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );
      
      // Should show connection status card
      expect(find.text('Connecting...'), findsOneWidget);
      expect(find.byIcon(Icons.sync), findsOneWidget);
    });

    testWidgets('Dashboard handles error states gracefully', (tester) async {
      // Mock API service that throws errors
      final errorApiService = _MockErrorApiService();
      
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiServiceProvider.overrideWithValue(errorApiService),
          ],
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );
      
      await tester.pump();
      
      // Should show error indicators
      expect(find.text('Connection Error'), findsWidgets);
    });

    testWidgets('Dashboard metrics have accessibility labels', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );
      
      await tester.pump();
      
      // Check for semantic labels on icons
      expect(find.bySemanticsLabel('Connection status'), findsOneWidget);
    });
  });
  
  group('Adaptive Polling Tests', () {
    testWidgets('Adaptive polling stops when widget is disposed', (tester) async {
      int callCount = 0;
      final mockApiService = _MockApiService(() => callCount++);
      
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiServiceProvider.overrideWithValue(mockApiService),
          ],
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );
      
      // Wait for initial polling
      await tester.pump(Duration(seconds: 1));
      final initialCallCount = callCount;
      
      // Navigate away (disposes the provider)
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(body: Text('Different screen')),
          ),
        ),
      );
      
      // Wait and verify no more calls
      await tester.pump(Duration(seconds: 20));
      expect(callCount, equals(initialCallCount));
    });
  });
}

class _MockApiService implements APIService {
  final VoidCallback? onCall;
  
  _MockApiService([this.onCall]);
  
  @override
  String get baseUrl => 'https://mock.api.com';
  
  @override
  Future<Map<String, dynamic>> getRealTimeData(String collarId) async {
    onCall?.call();
    return {
      'heart_rate': 80,
      'activity_level': 1,
      'location': {
        'type': 'Point',
        'coordinates': [-74.006, 40.7128]
      }
    };
  }
  
  @override
  Future<List<dynamic>> getPetTimeline(String collarId) async {
    return [
      {
        'timestamp': '2025-01-14T10:30:00Z',
        'behavior': 'Playing',
        'event_id': 'test-123'
      }
    ];
  }
  
  @override
  Future<Map<String, dynamic>> getPetPlan(String collarId) async {
    return {'plan': 'test'};
  }
  
  @override
  Future<void> submitFeedback(String eventId, String feedback) async {
    // Mock implementation
  }
}

class _MockErrorApiService implements APIService {
  @override
  String get baseUrl => 'https://error.api.com';
  
  @override
  Future<Map<String, dynamic>> getRealTimeData(String collarId) async {
    throw Exception('Network error');
  }
  
  @override
  Future<List<dynamic>> getPetTimeline(String collarId) async {
    throw Exception('Timeline error');
  }
  
  @override
  Future<Map<String, dynamic>> getPetPlan(String collarId) async {
    throw Exception('Plan error');
  }
  
  @override
  Future<void> submitFeedback(String eventId, String feedback) async {
    throw Exception('Feedback error');
  }
}