import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/widgets/glass_container.dart';

/// Simple validation test for GlassContainer parameter usage
void main() {
  group('GlassContainer Parameter Validation', () {
    testWidgets('accepts new opacity and borderAlpha parameters', (WidgetTester tester) async {
      // Test that we can create GlassContainer with new parameters
      const widget = GlassContainer(
        opacity: 0.25,
        borderAlpha: 0.4, 
        radius: 15,
        child: Text('Test'),
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: widget,
          ),
        ),
      );

      // Verify the widget renders without error
      expect(find.byType(GlassContainer), findsOneWidget);
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('uses default parameters when not specified', (WidgetTester tester) async {
      // Test that default parameters work (backward compatibility)
      const widget = GlassContainer(
        child: Text('Default Test'),
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: widget,
          ),
        ),
      );

      // Verify the widget renders without error
      expect(find.byType(GlassContainer), findsOneWidget);
      expect(find.text('Default Test'), findsOneWidget);
    });

    testWidgets('can override individual parameters', (WidgetTester tester) async {
      // Test partial parameter override
      const widget = GlassContainer(
        opacity: 0.08,  // Only override opacity
        child: Text('Partial Override Test'),
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: widget,
          ),
        ),
      );

      // Verify the widget renders without error
      expect(find.byType(GlassContainer), findsOneWidget);
      expect(find.text('Partial Override Test'), findsOneWidget);
    });
  });
}