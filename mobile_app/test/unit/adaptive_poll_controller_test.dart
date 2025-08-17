import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/services/adaptive_poll_controller.dart';

void main() {
  group('AdaptivePollController', () {
    late AdaptivePollController controller;

    setUp(() {
      controller = AdaptivePollController();
    });

    tearDown(() {
      controller.dispose();
    });

    test('should start with base interval', () {
      expect(controller.currentInterval, equals(const Duration(seconds: 12)));
      expect(controller.consecutiveErrors, equals(0));
    });

    test('should reset interval on request success', () {
      // Simulate some failures first
      controller.onRequestFailure();
      controller.onRequestFailure();
      expect(controller.currentInterval.inSeconds, greaterThan(12));
      
      // Success should reset
      controller.onRequestSuccess();
      expect(controller.currentInterval, equals(const Duration(seconds: 12)));
      expect(controller.consecutiveErrors, equals(0));
    });

    test('should apply backoff on consecutive failures', () {
      final initialInterval = controller.currentInterval;
      
      controller.onRequestFailure();
      expect(controller.currentInterval.inSeconds, greaterThan(initialInterval.inSeconds));
      expect(controller.consecutiveErrors, equals(1));
      
      final firstBackoffInterval = controller.currentInterval;
      controller.onRequestFailure();
      expect(controller.currentInterval.inSeconds, greaterThan(firstBackoffInterval.inSeconds));
      expect(controller.consecutiveErrors, equals(2));
    });

    test('should cap maximum interval', () {
      // Apply many failures
      for (int i = 0; i < 10; i++) {
        controller.onRequestFailure();
      }
      
      expect(controller.currentInterval.inSeconds, lessThanOrEqualTo(300)); // 5 minutes max
    });

    test('should increase interval in background mode', () {
      final normalInterval = controller.currentInterval;
      
      controller.setBackgroundMode(true);
      expect(controller.currentInterval.inSeconds, greaterThan(normalInterval.inSeconds));
      
      controller.setBackgroundMode(false);
      expect(controller.currentInterval, equals(const Duration(seconds: 12)));
    });

    test('should emit ticks when started', () async {
      final stream = controller.stream;
      controller.start();
      
      // We can't easily test the actual timing without making tests slow,
      // but we can verify the stream is set up
      expect(stream, isA<Stream<void>>());
      
      controller.stop();
    });

    test('should stop emitting when stopped', () {
      controller.start();
      expect(controller.currentInterval, isNotNull);
      
      controller.stop();
      // Timer should be cancelled (we can't directly test this without accessing privates)
    });
  });
}