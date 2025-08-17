import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/widgets/glass_container.dart';

/// Golden tests for GlassContainer widget variations
/// 
/// To update golden files when expected UI changes:
/// flutter test --update-goldens
/// 
/// Note: Golden tests are deterministic and should produce identical results
/// across different environments for reliable CI testing.
void main() {
  group('GlassContainer Golden Tests', () {
    testWidgets('default glass container appearance', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 300,
              height: 200,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter, 
                  end: Alignment.bottomCenter,
                ),
              ),
              child: const Center(
                child: GlassContainer(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text(
                      'Default Glass',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('glass_container_default.png'),
      );
    });

    testWidgets('high opacity glass container', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 300,
              height: 200,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter, 
                  end: Alignment.bottomCenter,
                ),
              ),
              child: const Center(
                child: GlassContainer(
                  opacity: 0.25,
                  borderAlpha: 0.4,
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text(
                      'High Opacity',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('glass_container_high_opacity.png'),
      );
    });

    testWidgets('low opacity glass container', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 300,
              height: 200,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter, 
                  end: Alignment.bottomCenter,
                ),
              ),
              child: const Center(
                child: GlassContainer(
                  opacity: 0.05,
                  borderAlpha: 0.1,
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text(
                      'Low Opacity',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('glass_container_low_opacity.png'),
      );
    });

    testWidgets('custom radius glass container', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 300,
              height: 200,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter, 
                  end: Alignment.bottomCenter,
                ),
              ),
              child: const Center(
                child: GlassContainer(
                  radius: 8,
                  opacity: 0.15,
                  borderAlpha: 0.3,
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text(
                      'Sharp Corners',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('glass_container_custom_radius.png'),
      );
    });

    testWidgets('glass container with metric content', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Container(
              width: 350,
              height: 120,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                  begin: Alignment.topCenter, 
                  end: Alignment.bottomCenter,
                ),
              ),
              child: const Center(
                child: GlassContainer(
                  child: Row(
                    children: [
                      Icon(Icons.favorite, color: Colors.white, size: 28),
                      SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              'Heart Rate',
                              style: TextStyle(
                                fontSize: 16,
                                color: Colors.white70,
                              ),
                            ),
                            SizedBox(height: 2),
                            Text(
                              '72 BPM',
                              style: TextStyle(
                                fontSize: 20,
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
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
        ),
      );

      await expectLater(
        find.byType(Container).first,
        matchesGoldenFile('glass_container_metric_content.png'),
      );
    });
  });
}