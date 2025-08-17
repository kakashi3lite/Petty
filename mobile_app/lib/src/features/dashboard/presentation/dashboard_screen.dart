import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../services/api_service.dart';
import '../../../widgets/glass_container.dart';

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
  
  late StreamController<Map<String, dynamic>> _realTimeController;
  Timer? _pollingTimer;
  Timer? _debounceTimer;
  DateTime? _lastUpdated;

  @override
  void initState() {
    super.initState();
    _realTimeController = StreamController<Map<String, dynamic>>.broadcast();
    _startPolling();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _debounceTimer?.cancel();
    _realTimeController.close();
    super.dispose();
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(const Duration(seconds: 15), (_) => _fetchRealTimeData());
    _fetchRealTimeData(); // Initial fetch
  }

  void _fetchRealTimeData() {
    // Cancel previous debounce timer if it exists
    _debounceTimer?.cancel();
    
    // Set up debounce timer (12 seconds minimum)
    _debounceTimer = Timer(const Duration(seconds: 12), () async {
      try {
        final data = await _service.getRealTimeData(_collarId);
        if (mounted) {
          setState(() {
            _lastUpdated = DateTime.now();
          });
          _realTimeController.add(data);
        }
      } catch (e) {
        if (mounted) {
          _realTimeController.add({"error": e.toString()});
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
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
                  if (_lastUpdated != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        'Last updated: ${_formatTime(_lastUpdated!)}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.white70,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  const SizedBox(height: 16),
                  Expanded(
                    child: StreamBuilder<Map<String, dynamic>>(
                      stream: _realTimeController.stream,
                      builder: (context, snapshot) {
                        if (snapshot.hasError) {
                          return Center(child: Text('Error: ${snapshot.error}', style: const TextStyle(color: Colors.white)));
                        }
                        
                        if (!snapshot.hasData) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        
                        final data = snapshot.data!;
                        final hr = data['heart_rate'] ?? '--';
                        final act = _describeActivity(data['activity_level']);
                        final loc = _describeLocation(data['location']);
                        return Column(
                          children: [
                            GlassContainer(child: _Metric(label: 'Heart Rate', value: '$hr BPM', icon: Icons.favorite)),
                            const SizedBox(height: 12),
                            GlassContainer(child: _Metric(label: 'Activity', value: act, icon: Icons.directions_run)),
                            const SizedBox(height: 12),
                            GlassContainer(child: _Metric(label: 'Location', value: loc, icon: Icons.location_on_outlined)),
                            const SizedBox(height: 16),
                            Align(
                              alignment: Alignment.centerLeft,
                              child: Text("Today's Story",
                                  style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white)),
                            ),
                            const SizedBox(height: 8),
                            Expanded(
                              child: timelineAsync.when(
                                data: (timeline) => ListView.builder(
                                  itemCount: timeline.length,
                                  itemBuilder: (ctx, i) {
                                    final ev = timeline[i] as Map<String, dynamic>;
                                    final ts = ev['timestamp'] ?? '';
                                    final label = ev['behavior'] ?? 'Event';
                                    final id = ev['event_id'] ?? 'id';
                                    final acked = _ack.contains(id);
                                    return Padding(
                                      padding: const EdgeInsets.only(bottom: 10),
                                      child: GlassContainer(
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
                                loading: () => const Center(child: CircularProgressIndicator()),
                                error: (e, _) => Text('timeline error: $e', style: const TextStyle(color: Colors.white)),
                              ),
                            ),
                          ],
                        );
                      },
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

  String _formatTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inSeconds < 60) {
      return '${difference.inSeconds}s ago';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else {
      return '${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}';
    }
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
