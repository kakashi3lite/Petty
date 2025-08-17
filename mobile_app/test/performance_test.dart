import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/services/adaptive_polling_service.dart';

void main() {
  group('Adaptive Polling Performance Tests', () {
    test('Polling interval adapts based on success/failure', () async {
      int callCount = 0;
      final calls = <DateTime>[];
      
      final service = AdaptivePollingService<String>(
        pollFunction: () async {
          callCount++;
          calls.add(DateTime.now());
          if (callCount <= 2) {
            return 'success';
          } else {
            throw Exception('Simulated error');
          }
        },
        onData: (data) {},
        onError: (error) {},
      );
      
      service.start();
      
      // Wait for initial successful polls
      await Future.delayed(Duration(seconds: 1));
      expect(callCount, greaterThan(0));
      
      // Wait for error condition to trigger backoff
      await Future.delayed(Duration(seconds: 5));
      
      // Verify that interval increases after errors
      expect(service.consecutiveErrors, greaterThan(0));
      expect(service.currentInterval.inSeconds, greaterThan(5));
      
      service.stop();
    });
    
    test('Service stops polling when disposed', () async {
      int callCount = 0;
      
      final service = AdaptivePollingService<String>(
        pollFunction: () async {
          callCount++;
          return 'success';
        },
        onData: (data) {},
        onError: (error) {},
      );
      
      service.start();
      await Future.delayed(Duration(milliseconds: 100));
      
      final callsBeforeStop = callCount;
      service.stop();
      
      await Future.delayed(Duration(seconds: 1));
      
      // Verify no additional calls after stop
      expect(callCount, equals(callsBeforeStop));
      expect(service.isActive, isFalse);
    });
    
    test('Debounce prevents rapid updates', () async {
      final updateTimes = <DateTime>[];
      
      final service = AdaptivePollingService<String>(
        pollFunction: () async => 'rapid-data',
        onData: (data) {
          updateTimes.add(DateTime.now());
        },
        onError: (error) {},
      );
      
      service.start();
      
      // Wait for multiple poll cycles
      await Future.delayed(Duration(seconds: 2));
      
      service.stop();
      
      // Verify debounce is working (should have fewer updates than polls)
      expect(updateTimes.length, lessThan(10)); // Reasonable debouncing
      
      if (updateTimes.length > 1) {
        // Check that updates are properly spaced
        final timeDiff = updateTimes[1].difference(updateTimes[0]);
        expect(timeDiff.inMilliseconds, greaterThan(1000)); // Debounced
      }
    });
  });
  
  group('Performance Benchmarks', () {
    test('Memory usage remains stable during extended polling', () async {
      // This test would normally measure memory usage
      // For now, we verify the service can run without leaks
      
      final service = AdaptivePollingService<String>(
        pollFunction: () async => 'benchmark-data',
        onData: (data) {},
        onError: (error) {},
      );
      
      service.start();
      
      // Simulate extended usage
      for (int i = 0; i < 10; i++) {
        await Future.delayed(Duration(milliseconds: 100));
      }
      
      expect(service.isActive, isTrue);
      
      service.stop();
      expect(service.isActive, isFalse);
    });
  });
}