import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/features/dashboard/presentation/pet_dashboard_screen.dart';

void main() {
  testWidgets('PetDashboard renders with main sections', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: PetDashboardScreen(),
      ),
    );
    
    // Wait for initial loading state
    await tester.pump();
    
    // Verify loading state shows
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    
    // Create screenshot for visual verification of loading state
    await expectLater(
      find.byType(PetDashboardScreen),
      matchesGoldenFile('pet_dashboard_loading.png'),
    );
    
    // Skip ahead to complete loading
    await tester.pump(const Duration(seconds: 3));
    
    // Verify loaded content
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Hello, User'), findsOneWidget);
    expect(find.text('Key Metrics'), findsOneWidget);
    expect(find.text('Recent Activity'), findsOneWidget);
    
    // Create screenshot of loaded state
    await expectLater(
      find.byType(PetDashboardScreen),
      matchesGoldenFile('pet_dashboard_loaded.png'),
    );
  });
}
