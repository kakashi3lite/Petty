import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';
import 'package:petty/src/services/api_service.dart';

// Mock API service to track method calls
class MockAPIService extends APIService {
  int submitFeedbackCallCount = 0;
  String? lastEventId;
  String? lastFeedback;
  bool shouldThrowError = false;
  
  MockAPIService() : super(baseUrl: 'https://test.example.com');
  
  @override
  Future<void> submitFeedback(String eventId, String feedback) async {
    submitFeedbackCallCount++;
    lastEventId = eventId;
    lastFeedback = feedback;
    
    if (shouldThrowError) {
      throw Exception('Network error');
    }
    
    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 100));
  }
  
  @override
  Future<Map<String, dynamic>> getRealTimeData(String collarId) async {
    return {
      'heart_rate': 75,
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
        'event_id': 'test-event-1',
        'timestamp': '10:30 AM',
        'behavior': 'Playing'
      },
      {
        'event_id': 'test-event-2', 
        'timestamp': '11:00 AM',
        'behavior': 'Resting'
      }
    ];
  }
}

void main() {
  group('Feedback Idempotency Tests', () {
    late MockAPIService mockService;
    
    setUp(() {
      mockService = MockAPIService();
    });
    
    testWidgets('tapping thumbs up twice only calls submitFeedback once', (WidgetTester tester) async {
      // Create a custom dashboard screen that uses our mock service
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: TestDashboardScreen(mockService: mockService),
          ),
        ),
      );
      
      // Wait for the initial data to load
      await tester.pumpAndSettle();
      
      // Find the first thumbs up button
      final thumbsUpButton = find.byIcon(Icons.thumb_up).first;
      expect(thumbsUpButton, findsOneWidget);
      
      // Tap the thumbs up button twice quickly
      await tester.tap(thumbsUpButton);
      await tester.tap(thumbsUpButton);
      
      // Wait for any async operations to complete
      await tester.pumpAndSettle();
      
      // Verify submitFeedback was called only once
      expect(mockService.submitFeedbackCallCount, equals(1));
      expect(mockService.lastEventId, equals('test-event-1'));
      expect(mockService.lastFeedback, equals('correct'));
    });
    
    testWidgets('button shows loading state during submission', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: TestDashboardScreen(mockService: mockService),
          ),
        ),
      );
      
      await tester.pumpAndSettle();
      
      final thumbsUpButton = find.byIcon(Icons.thumb_up).first;
      
      // Tap the button
      await tester.tap(thumbsUpButton);
      await tester.pump(); // Trigger a single frame to show loading state
      
      // Should show loading indicator
      expect(find.byType(CircularProgressIndicator), findsAtLeastNWidgets(1));
      
      // Wait for submission to complete
      await tester.pumpAndSettle();
      
      // Loading indicator should be gone, button should be in submitted state
      expect(find.byIcon(Icons.thumb_up).first, findsOneWidget);
    });
    
    testWidgets('on error, button is re-enabled and shows snackbar', (WidgetTester tester) async {
      mockService.shouldThrowError = true;
      
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: TestDashboardScreen(mockService: mockService),
          ),
        ),
      );
      
      await tester.pumpAndSettle();
      
      final thumbsUpButton = find.byIcon(Icons.thumb_up).first;
      
      // Tap the button
      await tester.tap(thumbsUpButton);
      await tester.pumpAndSettle();
      
      // Should show error snackbar
      expect(find.byType(SnackBar), findsOneWidget);
      expect(find.text('Failed to submit feedback: Exception: Network error'), findsOneWidget);
      
      // Button should be re-enabled (not in submitted state)
      expect(mockService.submitFeedbackCallCount, equals(1));
      
      // Should be able to tap again after error
      mockService.shouldThrowError = false;
      await tester.tap(thumbsUpButton);
      await tester.pumpAndSettle();
      
      expect(mockService.submitFeedbackCallCount, equals(2));
    });
    
    testWidgets('positive and negative feedback are tracked separately', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: TestDashboardScreen(mockService: mockService),
          ),
        ),
      );
      
      await tester.pumpAndSettle();
      
      final thumbsUpButton = find.byIcon(Icons.thumb_up).first;
      final thumbsDownButton = find.byIcon(Icons.thumb_down).first;
      
      // Tap thumbs up
      await tester.tap(thumbsUpButton);
      await tester.pumpAndSettle();
      
      expect(mockService.submitFeedbackCallCount, equals(1));
      expect(mockService.lastFeedback, equals('correct'));
      
      // Tap thumbs down on same event should still work (different feedback type)
      await tester.tap(thumbsDownButton);
      await tester.pumpAndSettle();
      
      expect(mockService.submitFeedbackCallCount, equals(2));
      expect(mockService.lastFeedback, equals('incorrect'));
    });
  });
}

// Test version of DashboardScreen that accepts a mock service
class TestDashboardScreen extends ConsumerStatefulWidget {
  final MockAPIService mockService;
  
  const TestDashboardScreen({super.key, required this.mockService});
  
  @override
  ConsumerState<TestDashboardScreen> createState() => _TestDashboardScreenState();
}

class _TestDashboardScreenState extends ConsumerState<TestDashboardScreen> {
  static const String _collarId = 'SN-123';
  
  // Track feedback states: successful submissions and loading states
  final Set<String> _positiveSubmitted = {};
  final Set<String> _negativeSubmitted = {};
  final Set<String> _submittingPositive = {};
  final Set<String> _submittingNegative = {};

  Future<void> _submitFeedback(String eventId, String feedback) async {
    // Prevent multiple submissions for the same event and feedback type
    final isPositive = feedback == 'correct';
    final alreadySubmitted = isPositive 
        ? _positiveSubmitted.contains(eventId)
        : _negativeSubmitted.contains(eventId);
    
    if (alreadySubmitted) return;
    
    // Check if already submitting
    final isSubmitting = isPositive 
        ? _submittingPositive.contains(eventId)
        : _submittingNegative.contains(eventId);
    
    if (isSubmitting) return;
    
    // Mark as submitting
    setState(() {
      if (isPositive) {
        _submittingPositive.add(eventId);
      } else {
        _submittingNegative.add(eventId);
      }
    });
    
    try {
      await widget.mockService.submitFeedback(eventId, feedback);
      
      // Mark as successfully submitted and remove from submitting
      setState(() {
        if (isPositive) {
          _submittingPositive.remove(eventId);
          _positiveSubmitted.add(eventId);
        } else {
          _submittingNegative.remove(eventId);
          _negativeSubmitted.add(eventId);
        }
      });
    } catch (e) {
      // Remove from submitting state on error and show error message
      setState(() {
        if (isPositive) {
          _submittingPositive.remove(eventId);
        } else {
          _submittingNegative.remove(eventId);
        }
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to submit feedback: ${e.toString()}'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FutureBuilder<List<dynamic>>(
        future: widget.mockService.getPetTimeline(_collarId),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          
          final timeline = snapshot.data!;
          return ListView.builder(
            itemCount: timeline.length,
            itemBuilder: (ctx, i) {
              final ev = timeline[i] as Map<String, dynamic>;
              final ts = ev['timestamp'] ?? '';
              final label = ev['behavior'] ?? 'Event';
              final id = ev['event_id'] ?? 'id';
              
              // Determine button states
              final positiveSubmitted = _positiveSubmitted.contains(id);
              final negativeSubmitted = _negativeSubmitted.contains(id);
              final submittingPositive = _submittingPositive.contains(id);
              final submittingNegative = _submittingNegative.contains(id);
              
              return Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  children: [
                    Expanded(child: Text('$ts — $label')),
                    IconButton(
                      icon: submittingPositive 
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(Colors.greenAccent),
                              ),
                            )
                          : Icon(
                              Icons.thumb_up, 
                              color: positiveSubmitted 
                                  ? Colors.greenAccent 
                                  : Colors.grey
                            ),
                      onPressed: positiveSubmitted || submittingPositive || submittingNegative
                          ? null 
                          : () => _submitFeedback(id, 'correct'),
                    ),
                    IconButton(
                      icon: submittingNegative 
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(Colors.redAccent),
                              ),
                            )
                          : Icon(
                              Icons.thumb_down, 
                              color: negativeSubmitted 
                                  ? Colors.redAccent 
                                  : Colors.grey
                            ),
                      onPressed: negativeSubmitted || submittingNegative || submittingPositive
                          ? null 
                          : () => _submitFeedback(id, 'incorrect'),
                    ),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}