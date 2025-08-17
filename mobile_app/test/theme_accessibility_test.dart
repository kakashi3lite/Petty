import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/theme/petty_theme.dart';
import 'package:petty/src/widgets/glassmorphism_components.dart';

void main() {
  group('Theme Tests', () {
    testWidgets('Dark theme has proper contrast ratios', (tester) async {
      final theme = PettyTheme.darkTheme();
      
      // Test contrast ratios for accessibility
      expect(
        PettyTheme.hasMinimumContrast(
          theme.colorScheme.onSurface,
          theme.colorScheme.surface,
        ),
        isTrue,
        reason: 'onSurface/surface contrast should be ≥4.5:1',
      );
      
      expect(
        PettyTheme.hasMinimumContrast(
          theme.colorScheme.onPrimary,
          theme.colorScheme.primary,
        ),
        isTrue,
        reason: 'onPrimary/primary contrast should be ≥4.5:1',
      );
    });
    
    testWidgets('Light theme has proper contrast ratios', (tester) async {
      final theme = PettyTheme.lightTheme();
      
      expect(
        PettyTheme.hasMinimumContrast(
          theme.colorScheme.onSurface,
          theme.colorScheme.surface,
        ),
        isTrue,
        reason: 'onSurface/surface contrast should be ≥4.5:1',
      );
    });
    
    testWidgets('Theme uses Material 3', (tester) async {
      final darkTheme = PettyTheme.darkTheme();
      final lightTheme = PettyTheme.lightTheme();
      
      expect(darkTheme.useMaterial3, isTrue);
      expect(lightTheme.useMaterial3, isTrue);
    });
    
    testWidgets('Theme has proper tap target sizes', (tester) async {
      final theme = PettyTheme.darkTheme();
      
      // Elevated buttons should have minimum 44x44 size
      final elevatedButtonStyle = theme.elevatedButtonTheme.style;
      final minimumSize = elevatedButtonStyle?.minimumSize?.resolve({});
      
      expect(minimumSize, isNotNull);
      expect(PettyTheme.hasMinimumTouchTarget(minimumSize!), isTrue);
    });
  });
  
  group('Glassmorphism Components Tests', () {
    testWidgets('GlassCard has proper accessibility', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: PettyTheme.darkTheme(),
          home: Scaffold(
            body: GlassCard(
              semanticLabel: 'Test card',
              onTap: () {},
              child: Text('Test content'),
            ),
          ),
        ),
      );
      
      // Should have semantic label
      expect(find.bySemanticsLabel('Test card'), findsOneWidget);
      
      // Should be marked as a button when tappable
      final semantics = tester.getSemantics(find.bySemanticsLabel('Test card'));
      expect(semantics.hasAction(SemanticsAction.tap), isTrue);
    });
    
    testWidgets('GlassButton has minimum touch target', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: PettyTheme.darkTheme(),
          home: Scaffold(
            body: GlassButton(
              onPressed: () {},
              child: Text('Test'),
            ),
          ),
        ),
      );
      
      final buttonSize = tester.getSize(find.byType(GlassButton));
      expect(PettyTheme.hasMinimumTouchTarget(buttonSize), isTrue);
    });
    
    testWidgets('GlassAppBar displays title correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: PettyTheme.darkTheme(),
          home: Scaffold(
            appBar: GlassAppBar(title: 'Test Title'),
            body: Container(),
          ),
        ),
      );
      
      expect(find.text('Test Title'), findsOneWidget);
    });
    
    testWidgets('GlassFloatingActionButton has semantic label', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: PettyTheme.darkTheme(),
          home: Scaffold(
            body: Container(),
            floatingActionButton: GlassFloatingActionButton(
              onPressed: () {},
              semanticLabel: 'Add item',
              child: Icon(Icons.add),
            ),
          ),
        ),
      );
      
      expect(find.bySemanticsLabel('Add item'), findsOneWidget);
    });
  });
  
  group('Accessibility Tests', () {
    testWidgets('Touch targets meet minimum size requirements', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: PettyTheme.darkTheme(),
          home: Scaffold(
            body: Column(
              children: [
                GlassButton(
                  onPressed: () {},
                  child: Text('Button'),
                ),
                GlassCard(
                  onTap: () {},
                  child: Text('Tappable card'),
                ),
              ],
            ),
          ),
        ),
      );
      
      // Check button size
      final buttonSize = tester.getSize(find.byType(GlassButton));
      expect(buttonSize.width, greaterThanOrEqualTo(44.0));
      expect(buttonSize.height, greaterThanOrEqualTo(44.0));
      
      // Check card tap target
      final cardWidget = find.byType(GlassCard);
      expect(cardWidget, findsOneWidget);
    });
    
    testWidgets('Semantic labels are present', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: PettyTheme.darkTheme(),
          home: Scaffold(
            body: Column(
              children: [
                GlassButton(
                  onPressed: () {},
                  semanticLabel: 'Submit form',
                  child: Text('Submit'),
                ),
                GlassCard(
                  semanticLabel: 'User profile',
                  child: Text('Profile info'),
                ),
              ],
            ),
          ),
        ),
      );
      
      expect(find.bySemanticsLabel('Submit form'), findsOneWidget);
      expect(find.bySemanticsLabel('User profile'), findsOneWidget);
    });
  });
}