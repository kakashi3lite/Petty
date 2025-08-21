import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/app.dart';

void main() {
  testWidgets('PettyApp can be instantiated and renders without errors', (tester) async {
    await tester.pumpWidget(const PettyApp());
    await tester.pump();
    
    // Should render the app without throwing errors
    expect(find.byType(MaterialApp), findsOneWidget);
    
    // Should show loading state initially for PetDashboardScreen
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('PettyApp shows pet dashboard after loading', (tester) async {
    await tester.pumpWidget(const PettyApp());
    await tester.pump();
    
    // Wait for loading to complete
    await tester.pump(const Duration(seconds: 3));
    
    // Should show the dashboard content
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Hello, User'), findsOneWidget);
    expect(find.text('Buddy'), findsOneWidget);
  });
}