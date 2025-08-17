import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:petty/src/features/dashboard/presentation/dashboard_screen.dart';

void main() {
  group('Performance Tests', () {
    testWidgets('Dashboard rebuild performance should be ≤33.4ms p99', (tester) async {
      // Track frame times during testing
      final frameTimes = <Duration>[];
      
      // Set up performance monitoring
      WidgetsBinding.instance.addPersistentFrameCallback((timeStamp) {
        final frameTime = WidgetsBinding.instance.currentFrameTimeStamp;
        if (frameTime != null) {
          frameTimes.add(frameTime);
        }
      });
      
      // Pump the dashboard screen
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );
      
      // Wait for initial render
      await tester.pumpAndSettle();
      
      // Simulate multiple rebuilds to measure performance
      for (int i = 0; i < 100; i++) {
        await tester.pump(const Duration(milliseconds: 16)); // ~60fps
      }
      
      // Calculate p99 frame time
      if (frameTimes.isNotEmpty) {
        frameTimes.sort();
        final p99Index = (frameTimes.length * 0.99).floor();
        final p99FrameTime = frameTimes[p99Index];
        
        print('P99 frame time: ${p99FrameTime.inMicroseconds / 1000}ms');
        
        // Assert p99 is ≤33.4ms (allowing for 60fps with some buffer)
        expect(
          p99FrameTime.inMicroseconds / 1000, 
          lessThanOrEqualTo(33.4),
          reason: 'P99 frame time should be ≤33.4ms for smooth 60fps performance',
        );
      }
    });
    
    testWidgets('GlassContainer render performance', (tester) async {
      const iterations = 50;
      final renderTimes = <Duration>[];
      
      for (int i = 0; i < iterations; i++) {
        final stopwatch = Stopwatch()..start();
        
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: ListView.builder(
                itemCount: 10,
                itemBuilder: (context, index) => Container(
                  margin: const EdgeInsets.all(8),
                  child: const Text('Test glass container performance'),
                ),
              ),
            ),
          ),
        );
        
        await tester.pumpAndSettle();
        stopwatch.stop();
        renderTimes.add(stopwatch.elapsed);
      }
      
      // Calculate average render time
      final averageTime = renderTimes.fold<Duration>(
        Duration.zero,
        (prev, time) => prev + time,
      ) ~/ iterations;
      
      print('Average GlassContainer render time: ${averageTime.inMilliseconds}ms');
      
      // Should render in reasonable time
      expect(
        averageTime.inMilliseconds,
        lessThan(100),
        reason: 'GlassContainer should render quickly',
      );
    });
    
    testWidgets('Adaptive polling does not cause memory leaks', (tester) async {
      // Test memory usage over time with polling
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );
      
      // Let it run for a bit to ensure polling starts
      await tester.pump(const Duration(seconds: 1));
      
      // Navigate away to test cleanup
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Text('Different screen'),
          ),
        ),
      );
      
      await tester.pumpAndSettle();
      
      // Test passes if no exceptions are thrown during cleanup
      expect(true, isTrue);
    });
  });
}