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
  
  // Track feedback states: successful submissions and loading states
  final Set<String> _positiveSubmitted = {};
  final Set<String> _negativeSubmitted = {};
  final Set<String> _submittingPositive = {};
  final Set<String> _submittingNegative = {};

  Future<void> _submitFeedback(String eventId, String feedback) async {
    // Prevent multiple submissions for the same event and feedback type
    final isPositive = feedback == 'correct';
    final alreadySubmitted = isPositive 
        ? _positiveSubmitted.contains(eventId)
        : _negativeSubmitted.contains(eventId);
    
    if (alreadySubmitted) return;
    
    // Check if already submitting
    final isSubmitting = isPositive 
        ? _submittingPositive.contains(eventId)
        : _submittingNegative.contains(eventId);
    
    if (isSubmitting) return;
    
    // Mark as submitting
    setState(() {
      if (isPositive) {
        _submittingPositive.add(eventId);
      } else {
        _submittingNegative.add(eventId);
      }
    });
    
    try {
      await _service.submitFeedback(eventId, feedback);
      
      // Mark as successfully submitted and remove from submitting
      setState(() {
        if (isPositive) {
          _submittingPositive.remove(eventId);
          _positiveSubmitted.add(eventId);
        } else {
          _submittingNegative.remove(eventId);
          _negativeSubmitted.add(eventId);
        }
      });
    } catch (e) {
      // Remove from submitting state on error and show error message
      setState(() {
        if (isPositive) {
          _submittingPositive.remove(eventId);
        } else {
          _submittingNegative.remove(eventId);
        }
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to submit feedback: ${e.toString()}'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final asyncData = ref.watch(_realTimeProvider);
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
                                    
                                    // Determine button states
                                    final positiveSubmitted = _positiveSubmitted.contains(id);
                                    final negativeSubmitted = _negativeSubmitted.contains(id);
                                    final submittingPositive = _submittingPositive.contains(id);
                                    final submittingNegative = _submittingNegative.contains(id);
                                    
                                    return Padding(
                                      padding: const EdgeInsets.only(bottom: 10),
                                      child: GlassContainer(
                                        child: Row(
                                          children: [
                                            Expanded(child: Text('$ts — $label', style: const TextStyle(color: Colors.white))),
                                            IconButton(
                                              icon: submittingPositive 
                                                  ? const SizedBox(
                                                      width: 16,
                                                      height: 16,
                                                      child: CircularProgressIndicator(
                                                        strokeWidth: 2,
                                                        valueColor: AlwaysStoppedAnimation<Color>(Colors.greenAccent),
                                                      ),
                                                    )
                                                  : Icon(
                                                      Icons.thumb_up, 
                                                      color: positiveSubmitted 
                                                          ? Colors.greenAccent 
                                                          : Colors.white70
                                                    ),
                                              onPressed: positiveSubmitted || submittingPositive || submittingNegative
                                                  ? null 
                                                  : () => _submitFeedback(id, 'correct'),
                                            ),
                                            IconButton(
                                              icon: submittingNegative 
                                                  ? const SizedBox(
                                                      width: 16,
                                                      height: 16,
                                                      child: CircularProgressIndicator(
                                                        strokeWidth: 2,
                                                        valueColor: AlwaysStoppedAnimation<Color>(Colors.redAccent),
                                                      ),
                                                    )
                                                  : Icon(
                                                      Icons.thumb_down, 
                                                      color: negativeSubmitted 
                                                          ? Colors.redAccent 
                                                          : Colors.white70
                                                    ),
                                              onPressed: negativeSubmitted || submittingNegative || submittingPositive
                                                  ? null 
                                                  : () => _submitFeedback(id, 'incorrect'),
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

  static final _realTimeProvider = StreamProvider<Map<String, dynamic>>((ref) async* {
    final service = APIService(baseUrl: _apiBaseUrl);
    while (true) {
      try { yield await service.getRealTimeData(_collarId); } catch (e) { yield {"error": e.toString()}; }
      await Future.delayed(const Duration(seconds: 15));
    }
  });

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
