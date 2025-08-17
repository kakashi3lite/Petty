import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
// find/expect come from flutter_test; no extra import needed, ensure ordering is top-only
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';

void main() {
  testWidgets('Dashboard shows last updated caption after data load', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    await tester.pump(const Duration(seconds: 16));
    expect(find.textContaining('Last updated:'), findsOneWidget);
  });
}
