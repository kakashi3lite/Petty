import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
// find/expect come from flutter_test; no extra import needed, ensure ordering is top-only
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';

void main() {
  testWidgets('Dashboard shows loading state initially', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    
    // Should show loading state initially
    expect(find.text('Loading dashboard...'), findsOneWidget);
  });
  
  testWidgets('Dashboard shows dashboard header', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DashboardScreen())));
    await tester.pump();
    
    // Should show the dashboard title
    expect(find.text('Real‑Time Dashboard'), findsOneWidget);
  });
}
