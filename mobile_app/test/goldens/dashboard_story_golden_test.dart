import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:golden_toolkit/golden_toolkit.dart';
import 'package:petty/src/widgets/glass_container.dart';

// Mock story event data structure based on dashboard_screen.dart
final mockStoryEvents = [
  {
    'timestamp': '08:30',
    'behavior': 'Morning Walk',
    'event_id': 'evt_001',
    'confidence': 0.95,
    'description': 'Pet went for morning exercise'
  },
  {
    'timestamp': '12:15',
    'behavior': 'Nap Time',
    'event_id': 'evt_002',
    'confidence': 0.88,
    'description': 'Pet is resting after lunch'
  },
  {
    'timestamp': '16:45',
    'behavior': 'Play Session',
    'event_id': 'evt_003',
    'confidence': 0.92,
    'description': 'Pet is actively playing'
  },
];

class MockStoryList extends StatefulWidget {
  final List<Map<String, dynamic>> events;
  final Set<String> acknowledgedEvents;

  const MockStoryList({
    super.key,
    required this.events,
    this.acknowledgedEvents = const {},
  });

  @override
  State<MockStoryList> createState() => _MockStoryListState();
}

class _MockStoryListState extends State<MockStoryList> {
  late Set<String> _acknowledged;

  @override
  void initState() {
    super.initState();
    _acknowledged = Set.from(widget.acknowledgedEvents);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          "Today's Story",
          style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: ListView.builder(
            itemCount: widget.events.length,
            itemBuilder: (ctx, i) {
              final event = widget.events[i];
              final timestamp = event['timestamp'] ?? '';
              final behavior = event['behavior'] ?? 'Event';
              final eventId = event['event_id'] ?? 'id';
              final acknowledged = _acknowledged.contains(eventId);
              
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: GlassContainer(
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          '$timestamp — $behavior',
                          style: const TextStyle(color: Colors.white),
                        ),
                      ),
                      IconButton(
                        icon: Icon(
                          Icons.thumb_up,
                          color: acknowledged ? Colors.greenAccent : Colors.white70,
                        ),
                        onPressed: () {
                          setState(() {
                            _acknowledged.add(eventId);
                          });
                        },
                      ),
                      IconButton(
                        icon: Icon(
                          Icons.thumb_down,
                          color: acknowledged ? Colors.redAccent : Colors.white70,
                        ),
                        onPressed: () {
                          setState(() {
                            _acknowledged.add(eventId);
                          });
                        },
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

void main() {
  group('Dashboard Story Golden Tests', () {
    testGoldens('Today\'s Story with multiple events', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: MaterialApp(
            home: Scaffold(
              body: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: MockStoryList(events: mockStoryEvents),
                  ),
                ),
              ),
            ),
          ),
          name: 'story_list_default',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'dashboard_story_list');
    });

    testGoldens('Today\'s Story with acknowledged events', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: MaterialApp(
            home: Scaffold(
              body: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: MockStoryList(
                      events: mockStoryEvents,
                      acknowledgedEvents: {'evt_001', 'evt_003'},
                    ),
                  ),
                ),
              ),
            ),
          ),
          name: 'story_list_acknowledged',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'dashboard_story_acknowledged');
    });

    testGoldens('Today\'s Story with custom glass styling', (tester) async {
      final customStoryList = Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Today's Story",
            style: ThemeData.light().textTheme.titleLarge?.copyWith(color: Colors.white),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView.builder(
              itemCount: mockStoryEvents.length,
              itemBuilder: (ctx, i) {
                final event = mockStoryEvents[i];
                final timestamp = event['timestamp'] ?? '';
                final behavior = event['behavior'] ?? 'Event';
                
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: GlassContainer(
                    opacity: 0.18,
                    borderAlpha: 0.35,
                    radius: 12,
                    child: Row(
                      children: [
                        Icon(
                          _getEventIcon(behavior),
                          color: Colors.white70,
                          size: 20,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            '$timestamp — $behavior',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            '${((event['confidence'] ?? 0.0) * 100).toInt()}%',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      );

      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: MaterialApp(
            home: Scaffold(
              body: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF1a1a2e), Color(0xFF16213e)],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: customStoryList,
                  ),
                ),
              ),
            ),
          ),
          name: 'story_list_custom_styling',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'dashboard_story_custom');
    });

    testGoldens('Today\'s Story loading and error states', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: const MaterialApp(
            home: Scaffold(
              body: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Today's Story",
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        SizedBox(height: 8),
                        Expanded(
                          child: Center(
                            child: CircularProgressIndicator(
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          name: 'loading_state',
        )
        ..addScenario(
          widget: const MaterialApp(
            home: Scaffold(
              body: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Today's Story",
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        SizedBox(height: 8),
                        Expanded(
                          child: Center(
                            child: Text(
                              'timeline error: Failed to load events',
                              style: TextStyle(color: Colors.white),
                              textAlign: TextAlign.center,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          name: 'error_state',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'dashboard_story_states');
    });
  });
}

IconData _getEventIcon(String behavior) {
  switch (behavior.toLowerCase()) {
    case 'morning walk':
    case 'walk':
      return Icons.directions_walk;
    case 'nap time':
    case 'sleep':
      return Icons.bedtime;
    case 'play session':
    case 'play':
      return Icons.sports_tennis;
    case 'feeding':
    case 'eat':
      return Icons.restaurant;
    default:
      return Icons.pets;
  }
}