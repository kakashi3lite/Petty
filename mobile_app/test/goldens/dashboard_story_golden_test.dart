import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/widgets/glass_container.dart';

/// Golden tests for dashboard story list with mocked events
/// 
/// To update golden files when expected UI changes:
/// flutter test --update-goldens
/// 
/// Note: Golden tests are deterministic and should produce identical results
/// across different environments for reliable CI testing.
void main() {
  group('Dashboard Story Golden Tests', () {
    // Mock event data for consistent testing
    final mockEvents = [
      {
        'event_id': 'evt_001',
        'timestamp': '2024-01-16 09:15',
        'behavior': 'Playing in backyard',
        'confidence': 0.89,
      },
      {
        'event_id': 'evt_002', 
        'timestamp': '2024-01-16 11:30',
        'behavior': 'Taking a nap',
        'confidence': 0.95,
      },
      {
        'event_id': 'evt_003',
        'timestamp': '2024-01-16 14:45',
        'behavior': 'Walking with owner',
        'confidence': 0.82,
      },
    ];

    testWidgets('story list with three events', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 400,
              height: 600,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Today's Story",
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: ListView.builder(
                        itemCount: mockEvents.length,
                        itemBuilder: (context, index) {
                          final event = mockEvents[index];
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: GlassContainer(
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      '${event['timestamp']} — ${event['behavior']}',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 16,
                                      ),
                                    ),
                                  ),
                                  IconButton(
                                    icon: const Icon(
                                      Icons.thumb_up,
                                      color: Colors.white70,
                                    ),
                                    onPressed: () {},
                                  ),
                                  IconButton(
                                    icon: const Icon(
                                      Icons.thumb_down,
                                      color: Colors.white70,
                                    ),
                                    onPressed: () {},
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('dashboard_story_three_events.png'),
      );
    });

    testWidgets('story list with acknowledged event', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 400,
              height: 400,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Today's Story",
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Single event with acknowledged state
                    GlassContainer(
                      child: Row(
                        children: [
                          const Expanded(
                            child: Text(
                              '2024-01-16 12:00 — Playing with favorite toy',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                              ),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(
                              Icons.thumb_up,
                              color: Colors.greenAccent, // Acknowledged state
                            ),
                            onPressed: () {},
                          ),
                          IconButton(
                            icon: const Icon(
                              Icons.thumb_down,
                              color: Colors.white70,
                            ),
                            onPressed: () {},
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    // Second event with negative feedback
                    GlassContainer(
                      child: Row(
                        children: [
                          const Expanded(
                            child: Text(
                              '2024-01-16 15:30 — Unusual behavior detected',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                              ),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(
                              Icons.thumb_up,
                              color: Colors.white70,
                            ),
                            onPressed: () {},
                          ),
                          IconButton(
                            icon: const Icon(
                              Icons.thumb_down,
                              color: Colors.redAccent, // Negative feedback state
                            ),
                            onPressed: () {},
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('dashboard_story_acknowledged_events.png'),
      );
    });

    testWidgets('empty story list state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 400,
              height: 300,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: const Padding(
                padding: EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Today's Story",
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(height: 16),
                    Expanded(
                      child: Center(
                        child: GlassContainer(
                          child: Padding(
                            padding: EdgeInsets.all(24.0),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.pets,
                                  size: 48,
                                  color: Colors.white70,
                                ),
                                SizedBox(height: 12),
                                Text(
                                  'No events today',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 18,
                                  ),
                                ),
                                SizedBox(height: 8),
                                Text(
                                  'Your pet is having a quiet day',
                                  style: TextStyle(
                                    color: Colors.white54,
                                    fontSize: 14,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('dashboard_story_empty_state.png'),
      );
    });

    testWidgets('story list with mixed confidence levels', (WidgetTester tester) async {
      final mixedConfidenceEvents = [
        {
          'event_id': 'evt_high',
          'timestamp': '2024-01-16 08:30',
          'behavior': 'Morning exercise (High confidence)',
          'confidence': 0.96,
        },
        {
          'event_id': 'evt_medium',
          'timestamp': '2024-01-16 13:15',
          'behavior': 'Possible rest period (Medium confidence)', 
          'confidence': 0.74,
        },
      ];

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 400,
              height: 300,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Today's Story",
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: ListView.builder(
                        itemCount: mixedConfidenceEvents.length,
                        itemBuilder: (context, index) {
                          final event = mixedConfidenceEvents[index];
                          final confidence = event['confidence'] as double;
                          
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: GlassContainer(
                              // Different opacity based on confidence
                              opacity: confidence > 0.9 ? 0.15 : 0.08,
                              borderAlpha: confidence > 0.9 ? 0.25 : 0.15,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          '${event['timestamp']} — ${event['behavior']}',
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 16,
                                          ),
                                        ),
                                      ),
                                      IconButton(
                                        icon: const Icon(
                                          Icons.thumb_up,
                                          color: Colors.white70,
                                        ),
                                        onPressed: () {},
                                      ),
                                      IconButton(
                                        icon: const Icon(
                                          Icons.thumb_down,
                                          color: Colors.white70,
                                        ),
                                        onPressed: () {},
                                      ),
                                    ],
                                  ),
                                  Padding(
                                    padding: const EdgeInsets.only(top: 4),
                                    child: Text(
                                      'Confidence: ${(confidence * 100).toInt()}%',
                                      style: const TextStyle(
                                        color: Colors.white54,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('dashboard_story_mixed_confidence.png'),
      );
    });
  });
}