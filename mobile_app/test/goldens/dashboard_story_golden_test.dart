import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../lib/src/features/dashboard/presentation/dashboard_screen.dart';
import '../../lib/src/widgets/glass_container.dart';

void main() {
  group('Dashboard Story Golden Tests', () {
    testWidgets('dashboard loading state', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Column(
                children: [
                  GlassContainer(
                    child: Column(
                      children: [
                        Text(
                          'Pet Dashboard',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 16),
                        CircularProgressIndicator(color: Colors.white),
                        SizedBox(height: 8),
                        Text(
                          'Loading real-time data...',
                          style: TextStyle(color: Colors.white70),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('dashboard_loading_story.png'),
      );
    });

    testWidgets('dashboard data display story', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Column(
                children: [
                  GlassContainer(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Pet Status',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 12),
                        Row(
                          children: [
                            Icon(Icons.favorite, color: Colors.red),
                            SizedBox(width: 8),
                            Text(
                              'Heart Rate: 75 BPM',
                              style: TextStyle(color: Colors.white),
                            ),
                          ],
                        ),
                        SizedBox(height: 8),
                        Row(
                          children: [
                            Icon(Icons.directions_run, color: Colors.green),
                            SizedBox(width: 8),
                            Text(
                              'Activity: Active',
                              style: TextStyle(color: Colors.white),
                            ),
                          ],
                        ),
                        SizedBox(height: 8),
                        Row(
                          children: [
                            Icon(Icons.location_on, color: Colors.blue),
                            SizedBox(width: 8),
                            Text(
                              'Location: (40.7128, -74.0060)',
                              style: TextStyle(color: Colors.white),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('dashboard_data_story.png'),
      );
    });

    testWidgets('glass container variants story', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Column(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                GlassContainer(
                  opacity: 0.1,
                  borderAlpha: 0.1,
                  child: Text(
                    'Subtle Glass',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                GlassContainer(
                  opacity: 0.2,
                  borderAlpha: 0.3,
                  child: Text(
                    'Medium Glass',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                GlassContainer(
                  opacity: 0.3,
                  borderAlpha: 0.5,
                  child: Text(
                    'Strong Glass',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('glass_variants_story.png'),
      );
    });
  });
}