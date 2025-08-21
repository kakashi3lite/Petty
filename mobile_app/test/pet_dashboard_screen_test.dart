import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:petty/src/features/dashboard/presentation/pet_dashboard_screen.dart';

void main() {
  group('PetDashboardScreen', () {
    testWidgets('should display loading indicator initially', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: PetDashboardScreen(),
        ),
      );

      // Should show loading indicator initially
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should display dashboard content after loading', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: PetDashboardScreen(),
        ),
      );

      // Wait for the future to complete
      await tester.pump(const Duration(seconds: 3));

      // Should find the dashboard content
      expect(find.text('Dashboard'), findsOneWidget);
      expect(find.text('Key Metrics'), findsOneWidget);
      expect(find.text('Recent Activity'), findsOneWidget);
    });

    test('MockPetDataService should return valid data', () async {
      final service = MockPetDataService();
      final viewModel = await service.getDashboardData();

      expect(viewModel.petName, equals('Buddy'));
      expect(viewModel.petStatusText, equals('Resting Calmly'));
      expect(viewModel.metrics.length, equals(3));
      expect(viewModel.activities.length, equals(3));
    });

    test('Metric model should store name correctly', () {
      final metric = Metric(name: 'Heart Rate');
      expect(metric.name, equals('Heart Rate'));
    });

    test('Activity model should store all properties correctly', () {
      final activity = Activity(
        icon: Icons.directions_run,
        name: 'Running',
        time: '10:00 AM',
        summary: 'Pet went for a run',
      );

      expect(activity.icon, equals(Icons.directions_run));
      expect(activity.name, equals('Running'));
      expect(activity.time, equals('10:00 AM'));
      expect(activity.summary, equals('Pet went for a run'));
    });
  });
}