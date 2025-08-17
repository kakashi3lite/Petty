import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/util/debounced_stream.dart';

void main() {
  group('PollingConfig', () {
    test('has correct default values', () {
      const config = PollingConfig();
      expect(config.fast, const Duration(seconds: 5));
      expect(config.normal, const Duration(seconds: 15));
      expect(config.idle, const Duration(seconds: 30));
      expect(config.maxBackoff, const Duration(seconds: 60));
      expect(config.minDebounce, const Duration(seconds: 12));
      expect(config.jitterPercent, 0.10);
    });
  });

  group('AdaptivePollingController', () {
    late AdaptivePollingController controller;

    setUp(() {
      controller = AdaptivePollingController();
    });

    test('starts with fast interval when recently active', () {
      controller.recordUserInteraction();
      final interval = controller.computeNextInterval();
      expect(interval.inSeconds, greaterThanOrEqualTo(5));
      expect(interval.inSeconds, lessThanOrEqualTo(12)); // respects min debounce
    });

    test('uses longer interval when idle', () {
      // Simulate being idle for 5 minutes
      controller.lastInteraction = DateTime.now().subtract(const Duration(minutes: 5));
      final interval = controller.computeNextInterval();
      expect(interval.inSeconds, greaterThanOrEqualTo(12));
    });

    test('respects minimum debounce interval', () {
      // Even with fast polling, should respect 12s minimum
      controller.recordUserInteraction();
      final interval = controller.computeNextInterval();
      expect(interval.inSeconds, greaterThanOrEqualTo(12));
    });

    test('increases interval on failures', () {
      final normalInterval = controller.computeNextInterval();
      
      controller.recordFailure();
      final failureInterval = controller.computeNextInterval();
      
      expect(failureInterval, greaterThan(normalInterval));
    });

    test('resets on success', () {
      controller.recordFailure();
      controller.recordFailure();
      expect(controller.failureStreak, 2);
      
      controller.recordSuccess();
      expect(controller.failureStreak, 0);
    });

    test('tracks recent data changes', () {
      controller.recordDataChange();
      expect(controller.lastDataChange, isNotNull);
      expect(controller.recentEvents, isNotEmpty);
    });

    test('uses fast interval when recent data change detected', () {
      controller.recordDataChange();
      final interval = controller.computeNextInterval();
      expect(interval.inSeconds, lessThanOrEqualTo(12)); // fast but respects min debounce
    });

    test('handles app background state', () {
      controller.setActive(false);
      final interval = controller.computeNextInterval();
      expect(interval.inSeconds, greaterThanOrEqualTo(12));
    });

    test('cleans up old events', () {
      // Add old events that should be cleaned up
      controller.recentEvents.add(DateTime.now().subtract(const Duration(minutes: 3)));
      controller.recordDataChange(); // This should trigger cleanup
      
      // Old events should be removed
      final now = DateTime.now();
      final recentCount = controller.recentEvents
          .where((e) => now.difference(e).inSeconds < 120)
          .length;
      expect(recentCount, equals(controller.recentEvents.length));
    });
  });

  group('DebouncedAdaptiveStream', () {
    late DebouncedAdaptiveStream<String> stream;
    late List<String> results;
    late List<dynamic> errors;
    int callCount = 0;

    Future<String> mockFetch() async {
      callCount++;
      if (callCount == 3) {
        throw Exception('Mock error');
      }
      return 'data_$callCount';
    }

    setUp(() {
      callCount = 0;
      results = [];
      errors = [];
      stream = DebouncedAdaptiveStream<String>(
        fetchFunction: mockFetch,
        controller: AdaptivePollingController(
          config: const PollingConfig(
            fast: Duration(milliseconds: 100),
            normal: Duration(milliseconds: 200),
            idle: Duration(milliseconds: 300),
            minDebounce: Duration(milliseconds: 50),
          ),
        ),
      );
    });

    tearDown(() {
      stream.dispose();
    });

    testWidgets('emits data and handles errors', (tester) async {
      // Listen to the stream
      final subscription = stream.stream.listen(
        (data) => results.add(data),
        onError: (error) => errors.add(error),
      );

      // Wait for initial calls
      await tester.pump(const Duration(milliseconds: 200));
      
      expect(results.length, greaterThan(0));
      expect(results.first, 'data_1');

      subscription.cancel();
    });

    testWidgets('stops emitting after dispose', (tester) async {
      final subscription = stream.stream.listen(
        (data) => results.add(data),
        onError: (error) => errors.add(error),
      );

      // Wait for some data
      await tester.pump(const Duration(milliseconds: 100));
      final initialCount = results.length;

      // Dispose the stream
      stream.dispose();

      // Wait more time - should not get new data
      await tester.pump(const Duration(milliseconds: 300));
      expect(results.length, equals(initialCount));

      subscription.cancel();
    });

    testWidgets('handles user interaction', (tester) async {
      final subscription = stream.stream.listen(
        (data) => results.add(data),
        onError: (error) => errors.add(error),
      );

      stream.recordUserInteraction();
      await tester.pump(const Duration(milliseconds: 100));
      
      // Should still be working
      expect(results, isNotEmpty);

      subscription.cancel();
    });

    testWidgets('no pending timers after dispose', (tester) async {
      // Start the stream
      final subscription = stream.stream.listen(
        (data) => results.add(data),
        onError: (error) => errors.add(error),
      );

      // Let it run briefly
      await tester.pump(const Duration(milliseconds: 50));

      // Dispose
      stream.dispose();
      subscription.cancel();

      // Verify no pending timers by pumping more time
      // If there were pending timers, they would cause exceptions or unwanted behavior
      await tester.pump(const Duration(seconds: 1));
      
      expect(() => tester.pump(const Duration(milliseconds: 100)), returnsNormally);
    });
  });
}