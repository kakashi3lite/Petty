import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../services/api_service.dart';
import '../../../widgets/glass_container.dart';
import '../../../widgets/glass_panel.dart';
import '../../../providers/adaptive_polling_provider.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  static const String _apiBaseUrl = 'https://api.example.com';
  static const String _collarId = 'SN-123';
  final _service = APIService(baseUrl: _apiBaseUrl);
  final Set<String> _ack = {};
    DateTime? _lastUpdated;

    @override
    void dispose() {
      // Cancel stream provider subscription by invalidating it (Riverpod manages cancellation)
      super.dispose();
    }

  @override
  Widget build(BuildContext context) {
    final asyncData = ref.watch(adaptiveRealTimeProvider(_collarId));
    final timelineAsync = ref.watch(_timelineProvider);
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                begin: Alignment.topCenter, end: Alignment.bottomCenter),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Real‑Time Dashboard',
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: Colors.white)),
                  const SizedBox(height: 16),
                  Expanded(
                    child: asyncData.when(
                      data: (data) {
                        final hr = data['heart_rate'] ?? '--';
                        final act = _describeActivity(data['activity_level']);
                        _lastUpdated = DateTime.now();
                        final loc = _describeLocation(data['location']);
                        return Column(
                          children: [
                            const SizedBox(height: 8),
                            if (_lastUpdated != null)
                              Align(
                                alignment: Alignment.centerLeft,
                                child: Text(
                                  'Last updated: ${_lastUpdated!.toLocal().toIso8601String()}',
                                  style: const TextStyle(fontSize: 12, color: Colors.white70),
                                ),
                              ),
                            const SizedBox(height: 16),
                            // Main metrics panel using GlassPanel
                            GlassPanel(
                              child: Column(
                                children: [
                                  _Metric(label: 'Heart Rate', value: '$hr BPM', icon: Icons.favorite),
                                  const SizedBox(height: 12),
                                  _Metric(label: 'Activity', value: act, icon: Icons.directions_run),
                                  const SizedBox(height: 12),
                                  _Metric(label: 'Location', value: loc, icon: Icons.location_on_outlined),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
                            Align(
                              alignment: Alignment.centerLeft,
                              child: Text("Today's Story",
                                  style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white)),
                            ),
                            const SizedBox(height: 8),
                            Expanded(
                              child: timelineAsync.when(
                                data: (timeline) => GlassPanel(
                                  child: ListView.builder(
                                    itemCount: timeline.length,
                                    itemBuilder: (ctx, i) {
                                      final ev = timeline[i] as Map<String, dynamic>;
                                      final ts = ev['timestamp'] ?? '';
                                      final label = ev['behavior'] ?? 'Event';
                                      final id = ev['event_id'] ?? 'id';
                                      final acked = _ack.contains(id);
                                      return Padding(
                                        padding: const EdgeInsets.only(bottom: 10),
                                        child: Container(
                                          padding: const EdgeInsets.all(12),
                                          decoration: BoxDecoration(
                                            color: Colors.white.withOpacity(0.08),
                                            borderRadius: BorderRadius.circular(8),
                                            border: Border.all(color: Colors.white.withOpacity(0.1)),
                                          ),
                                          child: Row(
                                            children: [
                                              Expanded(child: Text('$ts — $label', style: const TextStyle(color: Colors.white))),
                                              IconButton(
                                                icon: Icon(Icons.thumb_up, color: acked ? Colors.greenAccent : Colors.white70),
                                                onPressed: () async {
                                                  try { await _service.submitFeedback(id, 'correct'); setState(()=>_ack.add(id)); } catch (_) {}
                                                },
                                              ),
                                              IconButton(
                                                icon: Icon(Icons.thumb_down, color: acked ? Colors.redAccent : Colors.white70),
                                                onPressed: () async {
                                                  try { await _service.submitFeedback(id, 'incorrect'); setState(()=>_ack.add(id)); } catch (_) {}
                                                },
                                              ),
                                            ],
                                          ),
                                        ),
                                      );
                                    },
                                  ),
                                ),
                                loading: () => const Center(child: CircularProgressIndicator()),
                                error: (e, _) => Text('timeline error: $e', style: const TextStyle(color: Colors.white)),
                              ),
                            ),
                          ],
                        );
                      },
                      loading: () => const Center(child: CircularProgressIndicator()),
                      error: (e, _) => Center(child: Text('Error: $e', style: const TextStyle(color: Colors.white))),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  static String _describeActivity(dynamic level) {
    switch (level) {
      case 0: return 'Resting';
      case 1: return 'Walking';
      case 2: return 'Playing';
      default: return '--';
    }
  }

  static String _describeLocation(dynamic location) {
    if (location is Map<String, dynamic> && location.containsKey('coordinates')) {
      final coords = location['coordinates'] as List<dynamic>;
      return '(${coords[1].toStringAsFixed(4)}, ${coords[0].toStringAsFixed(4)})';
    }
    return '--';
  }

  static final _timelineProvider = FutureProvider<List<dynamic>>((ref) async {
    final service = APIService(baseUrl: _apiBaseUrl);
    return service.getPetTimeline(_collarId);
  });
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value, required this.icon});
  final String label; final String value; final IconData icon;
  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Icon(icon, color: Colors.white, size: 28),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: Theme.of(context).textTheme.titleMedium?.copyWith(color: Colors.white70)),
        const SizedBox(height: 2),
        Text(value, style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.bold)),
      ])),
    ]);
  }
}
