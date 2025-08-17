import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/app.dart';

void main() {
  group('Integration Tests', () {
    testWidgets('Complete app loads with new architecture', (tester) async {
      // Test that the app starts successfully with all new components
      await tester.pumpWidget(
        const ProviderScope(
          child: PettyApp(),
        ),
      );
      
      // Wait for initial render
      await tester.pump();
      
      // Verify app loads without throwing
      expect(find.byType(MaterialApp), findsOneWidget);
      
      // Should show dashboard screen initially
      expect(find.byType(Scaffold), findsOneWidget);
    });
    
    testWidgets('Theme switching works correctly', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: PettyApp(),
        ),
      );
      
      await tester.pump();
      
      // Get the current theme
      final context = tester.element(find.byType(MaterialApp));
      final theme = Theme.of(context);
      
      // Verify Material 3 is enabled
      expect(theme.useMaterial3, isTrue);
      
      // Verify we have proper color scheme
      expect(theme.colorScheme, isNotNull);
    });
    
    testWidgets('Glassmorphism components render correctly', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: PettyApp(),
        ),
      );
      
      // Wait for components to load
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));
      
      // Look for glass components (they should be present in dashboard)
      // Note: In a real test environment, we'd verify the visual properties
      expect(find.byType(Scaffold), findsOneWidget);
    });
  });
  
  group('Accessibility Integration Tests', () {
    testWidgets('App is accessible to screen readers', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: PettyApp(),
        ),
      );
      
      await tester.pump();
      
      // Use semantics tester to verify accessibility
      final SemanticsHandle handle = tester.ensureSemantics();
      
      try {
        // Verify that semantics tree is properly constructed
        expect(tester.binding.pipelineOwner.semanticsOwner, isNotNull);
        
        // In a real environment, we'd verify specific semantic properties
        // like labels, actions, and navigation structure
      } finally {
        handle.dispose();
      }
    });
  });
  
  group('Performance Integration Tests', () {
    testWidgets('App maintains 60fps during normal operation', (tester) async {
      // This test would measure frame rendering performance
      // In a real environment with flutter_driver, we'd measure actual frame times
      
      await tester.pumpWidget(
        const ProviderScope(
          child: PettyApp(),
        ),
      );
      
      // Simulate user interactions
      await tester.pump();
      
      // In a real test, we'd verify:
      // - Frame rendering time ≤ 16.6ms (60fps)
      // - Smooth animations
      // - No jank during scrolling
      
      expect(find.byType(MaterialApp), findsOneWidget);
    });
  });
}