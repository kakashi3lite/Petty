import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/features/help/presentation/help_screen.dart';

void main() {
  testWidgets('Help screen shows FAQ items and allows expand/collapse', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: HelpScreen()));
    
    // Verify the screen title is displayed
    expect(find.text('Help & FAQ'), findsOneWidget);
    
    // Verify all FAQ questions are displayed
    expect(find.text('Data Privacy'), findsOneWidget);
    expect(find.text('How Polling Works'), findsOneWidget);
    expect(find.text('What "Today\'s Story" Means'), findsOneWidget);
    expect(find.text('How 👍/👎 Trains the Model'), findsOneWidget);
    expect(find.text('Contact Support'), findsOneWidget);
    
    // Initially, answers should not be visible (collapsed state)
    expect(find.textContaining('Your pet\'s data is encrypted'), findsNothing);
    
    // Tap on the first FAQ item (Data Privacy) to expand it
    await tester.tap(find.text('Data Privacy'));
    await tester.pumpAndSettle();
    
    // Verify the answer is now visible
    expect(find.textContaining('Your pet\'s data is encrypted'), findsOneWidget);
    
    // Tap again to collapse
    await tester.tap(find.text('Data Privacy'));
    await tester.pumpAndSettle();
    
    // Verify the answer is hidden again
    expect(find.textContaining('Your pet\'s data is encrypted'), findsNothing);
    
    // Test expanding a different FAQ item
    await tester.tap(find.text('How Polling Works'));
    await tester.pumpAndSettle();
    
    // Verify this answer is visible
    expect(find.textContaining('The app automatically checks'), findsOneWidget);
  });
  
  testWidgets('Help screen back button works', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: const HelpScreen(),
      routes: {
        '/dashboard': (context) => const Scaffold(body: Text('Dashboard')),
      },
    ));
    
    // Find and tap the back button
    expect(find.byIcon(Icons.arrow_back), findsOneWidget);
    await tester.tap(find.byIcon(Icons.arrow_back));
    await tester.pumpAndSettle();
    
    // This test mainly verifies the back button is present and tappable
    // Navigation testing would require more complex setup with routing
  });
}