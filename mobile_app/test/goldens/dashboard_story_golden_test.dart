import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';

void main() {
  testWidgets('Dashboard renders with timeline story section', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: DashboardScreen(),
        ),
      ),
    );
    
    // Wait for initial loading state
    await tester.pump();
    
    // Verify initial structure (even during loading)
    expect(find.text('Real‑Time Dashboard'), findsOneWidget);
    expect(find.text('Today\'s Story'), findsOneWidget);
    
    // Create screenshot for visual verification
    await expectLater(
      find.byType(DashboardScreen),
      matchesGoldenFile('dashboard_loading.png'),
    );
    
    // Skip ahead to complete loading
    await tester.pump(const Duration(seconds: 5));
    
    // Create screenshot of loaded state
    await expectLater(
      find.byType(DashboardScreen),
      matchesGoldenFile('dashboard_loaded.png'),
    );
  });
}
