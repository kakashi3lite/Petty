# Flutter Test Notes

## Widget Testing

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

## Golden Testing

Golden tests capture visual snapshots of widgets to detect unintended UI changes. This project includes golden tests for the Glass UI components and dashboard elements.

### Running Golden Tests

To run all golden tests:
```bash
flutter test test/goldens/
```

To run a specific golden test file:
```bash
flutter test test/goldens/glass_container_golden_test.dart
flutter test test/goldens/dashboard_story_golden_test.dart
```

### Updating Golden Files

When UI changes are intentional, update the golden files to reflect the new expected appearance:

```bash
# Update all golden files
flutter test --update-goldens

# Update goldens for a specific test
flutter test --update-goldens test/goldens/glass_container_golden_test.dart
```

### Golden Test Best Practices

1. **Deterministic Content**: Use consistent, mocked data to ensure reproducible results
2. **Multiple Scenarios**: Test different states (loading, error, various data configurations)  
3. **Theme Variants**: Include both light and dark theme variations where applicable
4. **Device Coverage**: Test on different screen sizes when layout is responsive
5. **Accessibility**: Consider high contrast and accessibility modes in golden tests

### Golden Test Structure

Golden tests are organized in the `test/goldens/` directory:
- `glass_container_golden_test.dart` - Tests GlassContainer widget with various configurations
- `dashboard_story_golden_test.dart` - Tests "Today's Story" list component with mocked events

### CI/CD Integration

Golden tests should be stable on CI environments. If golden tests fail in CI:
1. Check if the failure is due to font rendering differences
2. Consider using a golden test toolkit with consistent fonts
3. Verify that all developers use the same Flutter version for golden generation

### Troubleshooting Golden Tests

- **Font Issues**: Ensure consistent fonts across development environments
- **Rendering Differences**: Use `goldenFileComparator` for custom comparison logic if needed
- **Test Failures**: Run `flutter test --update-goldens` locally and commit the updated files
- **CI Instability**: Consider using headless testing environments with consistent rendering
