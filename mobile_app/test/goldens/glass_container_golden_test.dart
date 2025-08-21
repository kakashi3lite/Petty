import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/widgets/glass_container.dart';

void main() {
  testWidgets('GlassContainer renders with default parameters', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: GlassContainer(
              child: Text('Default Glass'),
            ),
          ),
        ),
      ),
    );
    
    await expectLater(
      find.byType(GlassContainer),
      matchesGoldenFile('glass_container_default.png'),
    );
  });

  testWidgets('GlassContainer renders with custom opacity', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: GlassContainer(
              opacity: 0.25,
              borderAlpha: 0.4,
              child: Text('Custom Glass'),
            ),
          ),
        ),
      ),
    );
    
    await expectLater(
      find.byType(GlassContainer),
      matchesGoldenFile('glass_container_custom.png'),
    );
  });

  testWidgets('GlassContainer renders with custom radius', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: GlassContainer(
              radius: 10,
              padding: EdgeInsets.all(8),
              child: Text('Small Radius Glass'),
            ),
          ),
        ),
      ),
    );
    
    await expectLater(
      find.byType(GlassContainer),
      matchesGoldenFile('glass_container_small_radius.png'),
    );
  });
}
