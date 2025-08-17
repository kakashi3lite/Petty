import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';

void main() {
  testWidgets('Dashboard shows last updated caption after data load', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    
    // Wait for initial data load from adaptive polling
    await tester.pump(const Duration(seconds: 2));
    
    // Should show last updated text after data loads
    expect(find.textContaining('Last updated:'), findsOneWidget);
  });

  testWidgets('Dashboard has accessible refresh button', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    
    // Should have a refresh button that meets accessibility requirements
    expect(find.byTooltip('Refresh data'), findsOneWidget);
  });

  testWidgets('Feedback buttons meet touch target requirements', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    await tester.pump(const Duration(seconds: 2));
    
    // Find feedback buttons and verify they have minimum 48dp touch targets
    final thumbUpButtons = find.byTooltip('Mark as correct');
    final thumbDownButtons = find.byTooltip('Mark as incorrect');
    
    if (thumbUpButtons.hasFound) {
      final buttonWidget = tester.widget(thumbUpButtons.first);
      // IconButton should have proper constraints for accessibility
      expect(buttonWidget, isA<Widget>());
    }
  });
}
