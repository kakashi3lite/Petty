import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../../lib/src/widgets/glass_container.dart';

void main() {
  group('GlassContainer Golden Tests', () {
    testWidgets('default glass container', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: GlassContainer(
                child: Text(
                  'Default Glass Container',
                  style: TextStyle(color: Colors.white),
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('glass_container_default.png'),
      );
    });

    testWidgets('glass container with custom opacity', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: GlassContainer(
                opacity: 0.3,
                borderAlpha: 0.5,
                child: Text(
                  'Custom Opacity Container',
                  style: TextStyle(color: Colors.white),
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('glass_container_custom_opacity.png'),
      );
    });

    testWidgets('glass container with different radius', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: GlassContainer(
                radius: 10,
                child: Text(
                  'Small Radius Container',
                  style: TextStyle(color: Colors.white),
                ),
              ),
            ),
          ),
        ),
      );

      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('glass_container_small_radius.png'),
      );
    });
  });
}