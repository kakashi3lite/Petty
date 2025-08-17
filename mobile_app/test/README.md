# Flutter Test Notes

A widget test for the debounced real-time provider should:
1. Pump the `DashboardScreen` inside a `ProviderScope`.
2. Use a fake `APIService` injected via an override to count calls.
3. Dispose the widget (navigate away) and ensure no further calls after a delay greater than the poll interval.

Example skeleton (not executed here):
```dart
void main() {
  testWidgets('stops polling after dispose', (tester) async {
    final calls = <DateTime>[];
    final fake = FakeApiService(onCall: () => calls.add(DateTime.now()));
    await tester.pumpWidget(ProviderScope(overrides:[apiServiceProvider.overrideWithValue(fake)], child: const MaterialApp(home: DashboardScreen())));
    await tester.pump(const Duration(seconds:16));
    final countBefore = calls.length;
    // Remove widget
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump(const Duration(seconds:16));
    expect(calls.length, countBefore); // no new calls
  });
}
```
