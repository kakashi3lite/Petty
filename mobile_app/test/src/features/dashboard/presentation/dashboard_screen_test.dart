import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../lib/src/features/dashboard/presentation/dashboard_screen.dart';

void main() {
  group('DashboardScreen', () {
    testWidgets('should build and display dashboard elements', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );

      // Verify main elements are present
      expect(find.text('Real‑Time Dashboard'), findsOneWidget);
      expect(find.text("Today's Story"), findsOneWidget);
    });

    testWidgets('should dispose properly without errors', (WidgetTester tester) async {
      // Build the widget
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );

      // Verify widget is built
      expect(find.text('Real‑Time Dashboard'), findsOneWidget);

      // Dispose the widget by replacing it
      await tester.pumpWidget(
        MaterialApp(
          home: Container(),
        ),
      );
      
      // Pump to complete the disposal
      await tester.pump();

      // If we get here without errors, disposal worked correctly
      expect(find.text('Real‑Time Dashboard'), findsNothing);
    });

    testWidgets('should show loading state initially', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );

      // Should show loading indicator initially
      expect(find.byType(CircularProgressIndicator), findsAtLeastNWidgets(1));
    });
  });
}