import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/features/help/presentation/help_screen.dart';

void main() {
  group('HelpScreen', () {
    testWidgets('should display FAQ items', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: HelpScreen()));
      
      // Check that the help screen title is displayed
      expect(find.text('Help & FAQ'), findsOneWidget);
      
      // Check that at least one FAQ question is displayed
      expect(find.textContaining('How does pet behavior tracking work?'), findsOneWidget);
      expect(find.textContaining('What should I do if my pet\'s collar stops syncing?'), findsOneWidget);
    });

    testWidgets('should expand and collapse FAQ items when tapped', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: HelpScreen()));
      
      // Initially, answers should not be visible (collapsed state)
      expect(find.textContaining('Petty uses advanced sensors'), findsNothing);
      
      // Find and tap the first FAQ item
      final firstQuestion = find.textContaining('How does pet behavior tracking work?');
      expect(firstQuestion, findsOneWidget);
      
      await tester.tap(firstQuestion);
      await tester.pumpAndSettle(); // Wait for animation to complete
      
      // Now the answer should be visible (expanded state)
      expect(find.textContaining('Petty uses advanced sensors'), findsOneWidget);
      
      // Tap again to collapse
      await tester.tap(firstQuestion);
      await tester.pumpAndSettle();
      
      // Answer should be hidden again
      expect(find.textContaining('Petty uses advanced sensors'), findsNothing);
    });

    testWidgets('should allow multiple FAQ items to be expanded simultaneously', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: HelpScreen()));
      
      // Expand first FAQ item
      final firstQuestion = find.textContaining('How does pet behavior tracking work?');
      await tester.tap(firstQuestion);
      await tester.pumpAndSettle();
      
      // Expand second FAQ item
      final secondQuestion = find.textContaining('What should I do if my pet\'s collar stops syncing?');
      await tester.tap(secondQuestion);
      await tester.pumpAndSettle();
      
      // Both answers should be visible
      expect(find.textContaining('Petty uses advanced sensors'), findsOneWidget);
      expect(find.textContaining('First, check that the collar is charged'), findsOneWidget);
    });

    testWidgets('should show expand/collapse icons correctly', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: HelpScreen()));
      
      // Initially, should show expand_more icons
      expect(find.byIcon(Icons.expand_more), findsWidgets);
      expect(find.byIcon(Icons.expand_less), findsNothing);
      
      // Tap first FAQ item to expand
      final firstQuestion = find.textContaining('How does pet behavior tracking work?');
      await tester.tap(firstQuestion);
      await tester.pumpAndSettle();
      
      // Should now have at least one expand_less icon
      expect(find.byIcon(Icons.expand_less), findsOneWidget);
    });

    testWidgets('should have back button functionality', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: HelpScreen()));
      
      // Check that back button is present
      expect(find.byIcon(Icons.arrow_back), findsOneWidget);
      
      // Note: Navigation testing would require setting up GoRouter context
      // For now, we just verify the button exists
    });
  });
}