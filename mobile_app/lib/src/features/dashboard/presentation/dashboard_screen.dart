import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../services/api_service.dart';
import '../../../widgets/glass_container.dart';
import '../../../widgets/glassmorphism_components.dart';
import '../../../providers/data_providers.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  @override
  Widget build(BuildContext context) {
    final asyncData = ref.watch(adaptiveRealTimeProvider);
    final timelineAsync = ref.watch(timelineProvider);
    final lastUpdate = ref.watch(lastUpdateProvider);
    
    return Scaffold(
      appBar: const GlassAppBar(
        title: 'Pet Dashboard',
        automaticallyImplyLeading: false,
      ),
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
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Connection status indicator
                  GlassCard(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: Row(
                      children: [
                        Icon(
                          asyncData.when(
                            data: (data) => data.containsKey('error') 
                                ? Icons.error_outline 
                                : Icons.signal_cellular_4_bar,
                            loading: () => Icons.sync,
                            error: (_, __) => Icons.signal_cellular_off,
                          ),
                          color: asyncData.when(
                            data: (data) => data.containsKey('error') 
                                ? Colors.red 
                                : Colors.green,
                            loading: () => Colors.orange,
                            error: (_, __) => Colors.red,
                          ),
                          semanticLabel: 'Connection status',
                        ),
                        const SizedBox(width: 8),
                        Text(
                          asyncData.when(
                            data: (data) => data.containsKey('error') 
                                ? 'Connection Error' 
                                : 'Connected',
                            loading: () => 'Connecting...',
                            error: (_, __) => 'Disconnected',
                          ),
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const Spacer(),
                        if (lastUpdate != null)
                          Text(
                            'Last updated: ${lastUpdate.toString().substring(11, 19)}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Real-time metrics header
                  Text(
                    'Real‑Time Dashboard',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: Colors.white),
                  ),
                  const SizedBox(height: 16),
                  
                  // Real-time data section
                  asyncData.when(
                    data: (data) {
                      final hr = data['heart_rate'] ?? '--';
                      final act = _describeActivity(data['activity_level']);
                      final loc = _describeLocation(data['location']);
                      
                      // Update last update time
                      WidgetsBinding.instance.addPostFrameCallback((_) {
                        ref.read(lastUpdateProvider.notifier).state = DateTime.now();
                      });
                      
                      return Column(
                        children: [
                          // Metrics grid
                          Row(
                            children: [
                              Expanded(
                                child: GlassCard(
                                  child: _Metric(
                                    label: 'Heart Rate', 
                                    value: '$hr BPM', 
                                    icon: Icons.favorite,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: GlassCard(
                                  child: _Metric(
                                    label: 'Activity', 
                                    value: act, 
                                    icon: Icons.directions_run,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          GlassCard(
                            child: _Metric(
                              label: 'Location', 
                              value: loc, 
                              icon: Icons.location_on_outlined,
                            ),
                          ),
                          const SizedBox(height: 16),
                          // Timeline section
                          Text(
                            "Today's Story",
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white),
                          ),
                          const SizedBox(height: 12),
                          
                          // Timeline content
                          Container(
                            height: 300, // Fixed height for timeline
                            child: timelineAsync.when(
                              data: (timeline) => ListView.builder(
                                itemCount: timeline.length,
                                itemBuilder: (ctx, i) {
                                  final ev = timeline[i] as Map<String, dynamic>;
                                  final ts = ev['timestamp'] ?? '';
                                  final label = ev['behavior'] ?? 'Event';
                                  final id = ev['event_id'] ?? 'id';
                                  
                                  return Padding(
                                    padding: const EdgeInsets.only(bottom: 12),
                                    child: GlassCard(
                                      child: Row(
                                        children: [
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: [
                                                Text(
                                                  label,
                                                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                                    color: Colors.white,
                                                    fontWeight: FontWeight.w600,
                                                  ),
                                                ),
                                                const SizedBox(height: 4),
                                                Text(
                                                  ts,
                                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                                    color: Colors.white70,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                          // Feedback buttons with accessibility
                                          GlassButton(
                                            onPressed: () async {
                                              try {
                                                final apiService = ref.read(apiServiceProvider);
                                                await apiService.submitFeedback(id, 'correct');
                                              } catch (e) {
                                                // Handle error silently for now
                                              }
                                            },
                                            semanticLabel: 'Mark as correct',
                                            minimumSize: const Size(44, 44),
                                            child: const Icon(Icons.thumb_up, size: 20),
                                          ),
                                          const SizedBox(width: 8),
                                          GlassButton(
                                            onPressed: () async {
                                              try {
                                                final apiService = ref.read(apiServiceProvider);
                                                await apiService.submitFeedback(id, 'incorrect');
                                              } catch (e) {
                                                // Handle error silently for now
                                              }
                                            },
                                            semanticLabel: 'Mark as incorrect',
                                            minimumSize: const Size(44, 44),
                                            child: const Icon(Icons.thumb_down, size: 20),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                },
                              ),
                              loading: () => const Center(
                                child: CircularProgressIndicator(
                                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                ),
                              ),
                              error: (e, _) => GlassCard(
                                child: Text(
                                  'Timeline error: $e',
                                  style: const TextStyle(color: Colors.white),
                                ),
                              ),
                            ),
                        ],
                      );
                    },
                    loading: () => const Center(
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                    error: (e, _) => GlassCard(
                      child: Text(
                        'Error: $e',
                        style: const TextStyle(color: Colors.white),
                      ),
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
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value, required this.icon});
  final String label; 
  final String value; 
  final IconData icon;
  
  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label: $value',
      child: Column(
        children: [
          Icon(
            icon, 
            color: Colors.white, 
            size: 32,
            semanticLabel: label,
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.white70,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
