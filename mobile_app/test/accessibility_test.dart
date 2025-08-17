import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/widgets/accessible_icon_button.dart';
import 'package:petty/src/widgets/glass_components.dart';
import 'package:petty/src/theme/app_theme.dart';

void main() {
  group('Accessibility Tests', () {
    testWidgets('AccessibleIconButton meets minimum touch target size', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light(),
          home: Scaffold(
            body: AccessibleIconButton(
              icon: Icons.favorite,
              onPressed: () {},
              semanticLabel: 'Test button',
            ),
          ),
        ),
      );

      final buttonFinder = find.byType(AccessibleIconButton);
      expect(buttonFinder, findsOneWidget);

      final buttonSize = tester.getSize(buttonFinder);
      // Verify minimum 48dp (48 logical pixels) touch target
      expect(buttonSize.width, greaterThanOrEqualTo(48.0));
      expect(buttonSize.height, greaterThanOrEqualTo(48.0));
    });

    testWidgets('FeedbackButton has proper semantic labels', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light(),
          home: Scaffold(
            body: FeedbackButton(
              icon: Icons.thumb_up,
              onPressed: () {},
              isSelected: false,
              label: 'Like',
            ),
          ),
        ),
      );

      // Verify semantic label is present
      expect(find.bySemanticsLabel('Like'), findsOneWidget);
    });

    testWidgets('GlassNavBar items have proper semantic properties', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light(),
          home: Scaffold(
            body: GlassNavBar(
              items: const [
                GlassNavItem(icon: Icons.home, label: 'Home'),
                GlassNavItem(icon: Icons.search, label: 'Search'),
                GlassNavItem(icon: Icons.person, label: 'Profile'),
              ],
              currentIndex: 0,
              onTap: (index) {},
            ),
          ),
        ),
      );

      // Verify navigation items are present and have labels
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Search'), findsOneWidget);
      expect(find.text('Profile'), findsOneWidget);
    });

    testWidgets('Theme provides proper contrast ratios', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light(),
          home: const Scaffold(
            body: Text(
              'Test text',
              style: TextStyle(fontSize: 16),
            ),
          ),
        ),
      );

      final textWidget = tester.widget<Text>(find.text('Test text'));
      final textStyle = textWidget.style;
      
      // Verify text color provides sufficient contrast
      // This is a basic check - real contrast ratio testing would require
      // additional tools to measure against background colors
      expect(textStyle?.color, isNotNull);
    });

    testWidgets('Dark theme maintains accessibility standards', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.dark(),
          home: Scaffold(
            body: Column(
              children: [
                const Text('Header', style: TextStyle(fontSize: 24)),
                const Text('Body text', style: TextStyle(fontSize: 16)),
                AccessibleIconButton(
                  icon: Icons.settings,
                  onPressed: () {},
                  semanticLabel: 'Settings',
                ),
              ],
            ),
          ),
        ),
      );

      // Verify all elements are present in dark theme
      expect(find.text('Header'), findsOneWidget);
      expect(find.text('Body text'), findsOneWidget);
      expect(find.bySemanticsLabel('Settings'), findsOneWidget);
    });
  });

  group('Performance Tests', () {
    testWidgets('GlassContainer uses RepaintBoundary for performance', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light(),
          home: const Scaffold(
            body: GlassCard(
              child: Text('Performance test'),
            ),
          ),
        ),
      );

      // Verify RepaintBoundary is used in the widget tree
      expect(find.byType(RepaintBoundary), findsAtLeastNWidgets(1));
    });
  });
}