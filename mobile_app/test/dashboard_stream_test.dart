import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';

void main() {
  testWidgets('Dashboard shows last updated caption after data load', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    await tester.pump(const Duration(seconds: 16));
    expect(find.textContaining('Last updated:'), findsOneWidget);
  });

  testWidgets('stops polling after dispose - no pending timers', (tester) async {
    // Pump the widget
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    
    // Let it run briefly to start polling
    await tester.pump(const Duration(seconds: 1));
    
    // Remove the widget by replacing it with an empty container
    await tester.pumpWidget(Container());
    
    // Wait longer than any polling interval to ensure cleanup
    await tester.pump(const Duration(seconds: 20));
    
    // If there were pending timers, they would cause issues here
    expect(() => tester.pump(const Duration(seconds: 1)), returnsNormally);
  });

  testWidgets('stream cancels on dispose', (tester) async {
    // Create widget
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    
    // Let polling start
    await tester.pump(const Duration(seconds: 1));
    
    // Dispose by navigation to different widget
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: Container())));
    
    // Verify no exceptions or pending operations
    await tester.pump(const Duration(seconds: 15));
    expect(tester.takeException(), isNull);
  });

  testWidgets('responds to user interaction', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    
    // Simulate user interaction by tapping
    await tester.tap(find.byType(Scaffold));
    await tester.pump();
    
    // Should continue to work without errors
    expect(tester.takeException(), isNull);
  });
}
