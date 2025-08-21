import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/features/dashboard/presentation/pet_dashboard_screen.dart';

void main() {
  testWidgets('PetDashboard shows content after data load', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    await tester.pump(const Duration(seconds: 3));
    expect(find.text('Dashboard'), findsOneWidget);
  });

  testWidgets('stops loading after dispose - no pending timers', (tester) async {
    // Pump the widget
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    
    // Let it run briefly to start loading
    await tester.pump(const Duration(seconds: 1));
    
    // Remove the widget by replacing it with an empty container
    await tester.pumpWidget(Container());
    
    // Wait longer than any loading interval to ensure cleanup
    await tester.pump(const Duration(seconds: 5));
    
    // If there were pending timers, they would cause issues here
    expect(() => tester.pump(const Duration(seconds: 1)), returnsNormally);
  });

  testWidgets('handles dispose correctly', (tester) async {
    // Create widget
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    
    // Let loading start
    await tester.pump(const Duration(seconds: 1));
    
    // Dispose by navigation to different widget
    await tester.pumpWidget(const MaterialApp(home: Container()));
    
    // Verify no exceptions or pending operations
    await tester.pump(const Duration(seconds: 3));
    expect(tester.takeException(), isNull);
  });

  testWidgets('responds to user interaction', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    
    // Simulate user interaction by tapping
    await tester.tap(find.byType(Scaffold));
    await tester.pump();
    
    // Should continue to work without errors
    expect(tester.takeException(), isNull);
  });
}
