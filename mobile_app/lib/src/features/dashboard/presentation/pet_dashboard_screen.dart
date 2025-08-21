import 'package:flutter/material.dart';
import '../../../design_system.dart';
import '../../../components.dart';
import 'dart:async';

class PetDashboardScreen extends StatefulWidget {
  const PetDashboardScreen({super.key});

  @override
  State<PetDashboardScreen> createState() => _PetDashboardScreenState();
}

class _PetDashboardScreenState extends State<PetDashboardScreen> {
  late Future<PetDashboardViewModel> _viewModelFuture;

  @override
  void initState() {
    super.initState();
    _viewModelFuture = MockPetDataService().getDashboardData();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBackgroundColor,
      body: FutureBuilder<PetDashboardViewModel>(
        future: _viewModelFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(
              child: LoadingStateIndicator(),
            );
          } else if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('Error: ${snapshot.error}', style: AppTypography.body),
                  const SizedBox(height: kSpacingUnit * 2),
                  PrimaryActionButton(
                    text: 'Retry',
                    onPressed: () {
                      setState(() {
                        _viewModelFuture = MockPetDataService().getDashboardData();
                      });
                    },
                  ),
                ],
              ),
            );
          } else if (snapshot.hasData) {
            final viewModel = snapshot.data!;
            return CustomScrollView(
              slivers: [
                SliverAppBar(
                  pinned: true,
                  expandedHeight: 150.0,
                  backgroundColor: kPrimaryColor,
                  flexibleSpace: FlexibleSpaceBar(
                    title: Text(
                      'Dashboard\nHello, User',
                      style: AppTypography.h2.copyWith(color: Colors.white),
                    ),
                  ),
                ),
                SliverPadding(
                  padding: const EdgeInsets.all(kSpacingUnit * 2),
                  sliver: SliverToBoxAdapter(
                    child: PetStatusCard(
                      petName: viewModel.petName,
                      avatarUrl: viewModel.petAvatarUrl,
                      statusText: viewModel.petStatusText,
                    ),
                  ),
                ),
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: kSpacingUnit * 2),
                    child: Text("Key Metrics", style: AppTypography.h2),
                  ),
                ),
                SliverToBoxAdapter(
                  child: SizedBox(
                    height: 200,
                    child: ListView.separated(
                      padding: const EdgeInsets.all(kSpacingUnit * 2),
                      scrollDirection: Axis.horizontal,
                      itemCount: viewModel.metrics.length,
                      separatorBuilder: (context, index) => const SizedBox(width: kSpacingUnit * 2),
                      itemBuilder: (context, index) {
                        final metric = viewModel.metrics[index];
                        return HealthMetricChartCard(title: metric.name,);
                      },
                    ),
                  ),
                ),
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(kSpacingUnit * 2),
                    child: Text("Recent Activity", style: AppTypography.h2),
                  ),
                ),
                SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final activity = viewModel.activities[index];
                      return Padding(
                        padding: const EdgeInsets.symmetric(horizontal: kSpacingUnit * 2),
                        child: ActivityTimelineTile(
                          icon: activity.icon,
                          activityName: activity.name,
                          time: activity.time,
                          summary: activity.summary,
                          isFirst: index == 0,
                          isLast: index == viewModel.activities.length - 1,
                        ),
                      );
                    },
                    childCount: viewModel.activities.length,
                  ),
                ),
              ],
            );
          } else {
            return const Center(child: Text("No data available"));
          }
        },
      ),
    );
  }
}

class HealthMetricChartCard extends StatelessWidget {
  final String title;
  const HealthMetricChartCard({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 300,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(kBorderRadius),
        boxShadow: [kSoftShadow],
      ),
      child: Padding(
        padding: const EdgeInsets.all(kSpacingUnit * 2),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: AppTypography.h2.copyWith(fontSize: 18)),
            const SizedBox(height: kSpacingUnit),
            const Expanded(
              child: HealthMetricChart(),
            ),
          ],
        ),
      ),
    );
  }
}

class PetDashboardViewModel {
  final String petName;
  final String petAvatarUrl;
  final String petStatusText;
  final List<Metric> metrics;
  final List<Activity> activities;

  PetDashboardViewModel({
    required this.petName,
    required this.petAvatarUrl,
    required this.petStatusText,
    required this.metrics,
    required this.activities,
  });
}

class Metric {
  final String name;

  Metric({required this.name});
}

class Activity {
  final IconData icon;
  final String name;
  final String time;
  final String summary;

  Activity({
    required this.icon,
    required this.name,
    required this.time,
    required this.summary,
  });
}

class MockPetDataService {
  Future<PetDashboardViewModel> getDashboardData() async {
    await Future.delayed(const Duration(seconds: 2));

    return PetDashboardViewModel(
      petName: "Buddy",
      petAvatarUrl: "https://images.dog.ceo/breeds/hound-afghan/n02088094_1026.jpg",
      petStatusText: "Resting Calmly",
      metrics: [
        Metric(name: "Heart Rate"),
        Metric(name: "Activity Level"),
        Metric(name: "Sleep Quality"),
      ],
      activities: [
        Activity(icon: Icons.directions_run, name: "High-Energy Play", time: "10:30 AM", summary: "Chased squirrels in the park."),
        Activity(icon: Icons.local_restaurant, name: "Lunch Time", time: "12:00 PM", summary: "Enjoyed a tasty meal."),
        Activity(icon: Icons.nightlight_round, name: "Nap Time", time: "2:00 PM", summary: "Took a peaceful nap."),
      ],
    );
  }
}