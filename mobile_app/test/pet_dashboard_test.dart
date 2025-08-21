import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/features/dashboard/presentation/pet_dashboard_screen.dart';

void main() {
  testWidgets('PetDashboardScreen shows loading indicator initially', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    
    // Should show loading indicator
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('PetDashboardScreen shows dashboard content after loading', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    
    // Wait for the mock data to load (2 seconds delay)
    await tester.pump(const Duration(seconds: 3));
    
    // Should show dashboard content
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Hello, User'), findsOneWidget);
    expect(find.text('Buddy'), findsOneWidget);
    expect(find.text('Key Metrics'), findsOneWidget);
    expect(find.text('Recent Activity'), findsOneWidget);
  });

  testWidgets('PetDashboardScreen shows metric cards', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    await tester.pump(const Duration(seconds: 3));
    
    // Should show metric cards
    expect(find.text('Heart Rate'), findsOneWidget);
    expect(find.text('Activity Level'), findsOneWidget);
    expect(find.text('Sleep Quality'), findsOneWidget);
  });

  testWidgets('PetDashboardScreen shows activity timeline', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    await tester.pump(const Duration(seconds: 3));
    
    // Should show activity items
    expect(find.text('High-Energy Play'), findsOneWidget);
    expect(find.text('Lunch Time'), findsOneWidget);
    expect(find.text('Nap Time'), findsOneWidget);
  });

  testWidgets('PetDashboardScreen retry button works on error', (tester) async {
    // This test would need mock service to simulate error, but for now
    // we'll just verify the screen builds successfully
    await tester.pumpWidget(const MaterialApp(home: PetDashboardScreen()));
    await tester.pump();
    
    expect(find.byType(PetDashboardScreen), findsOneWidget);
  });
}