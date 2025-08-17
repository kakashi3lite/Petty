import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/widgets/glass_container.dart';

void main() {
  group('GlassContainer Widget Tests', () {
    testWidgets('creates glass container with default parameters', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: GlassContainer(
              child: Text('Test Content'),
            ),
          ),
        ),
      );

      expect(find.text('Test Content'), findsOneWidget);
      expect(find.byType(GlassContainer), findsOneWidget);
    });

    testWidgets('creates glass container with custom parameters', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: GlassContainer(
              opacity: 0.25,
              borderAlpha: 0.5,
              radius: 15,
              padding: EdgeInsets.all(24),
              child: Text('Custom Glass'),
            ),
          ),
        ),
      );

      expect(find.text('Custom Glass'), findsOneWidget);
      expect(find.byType(GlassContainer), findsOneWidget);
    });

    testWidgets('validates parameter constraints', (tester) async {
      // Test that invalid parameters throw assertions
      expect(
        () => GlassContainer(
          opacity: -0.1, // Invalid: negative opacity
          child: const Text('Test'),
        ),
        throwsAssertionError,
      );

      expect(
        () => GlassContainer(
          opacity: 1.1, // Invalid: opacity > 1.0
          child: const Text('Test'),
        ),
        throwsAssertionError,
      );

      expect(
        () => GlassContainer(
          borderAlpha: -0.1, // Invalid: negative borderAlpha
          child: const Text('Test'),
        ),
        throwsAssertionError,
      );

      expect(
        () => GlassContainer(
          borderAlpha: 1.1, // Invalid: borderAlpha > 1.0
          child: const Text('Test'),
        ),
        throwsAssertionError,
      );

      expect(
        () => GlassContainer(
          radius: -5, // Invalid: negative radius
          child: const Text('Test'),
        ),
        throwsAssertionError,
      );
    });

    testWidgets('maintains backward compatibility with existing usage', (tester) async {
      // This test ensures that existing code using GlassContainer without
      // the new parameters continues to work as before
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: GlassContainer(
              child: Row(
                children: [
                  Icon(Icons.favorite, color: Colors.white),
                  SizedBox(width: 12),
                  Text('Heart Rate: 85 BPM', style: TextStyle(color: Colors.white)),
                ],
              ),
            ),
          ),
        ),
      );

      expect(find.text('Heart Rate: 85 BPM'), findsOneWidget);
      expect(find.byIcon(Icons.favorite), findsOneWidget);
      expect(find.byType(GlassContainer), findsOneWidget);
    });
  });
}