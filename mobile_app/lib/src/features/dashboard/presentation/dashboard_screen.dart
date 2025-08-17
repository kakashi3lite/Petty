import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../services/api_service.dart';
import '../../../services/adaptive_polling_service.dart';
import '../../../services/offline_cache_service.dart';
import '../../../widgets/glass_container.dart';
import '../../../widgets/accessible_icon_button.dart';
import '../../../theme/glassmorphism_theme.dart';

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

  String _formatTimestamp(String timestamp) {
    try {
      final dateTime = DateTime.parse(timestamp);
      final now = DateTime.now();
      final difference = now.difference(dateTime);
      
      if (difference.inDays > 0) {
        return '${difference.inDays} day${difference.inDays == 1 ? '' : 's'} ago';
      } else if (difference.inHours > 0) {
        return '${difference.inHours} hour${difference.inHours == 1 ? '' : 's'} ago';
      } else if (difference.inMinutes > 0) {
        return '${difference.inMinutes} minute${difference.inMinutes == 1 ? '' : 's'} ago';
      } else {
        return 'Just now';
      }
    } catch (e) {
      return timestamp; // Fallback to original timestamp
    }
  }

  @override
  Widget build(BuildContext context) {
    final asyncData = ref.watch(_realTimeProvider);
    final timelineAsync = ref.watch(_timelineProvider);
    final glassTheme = context.glassTheme;
    
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),
          RepaintBoundary(
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Real‑Time Dashboard',
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        color: glassTheme.onSurfaceColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: asyncData.when(
                        data: (data) {
                          if (data.containsKey('error')) {
                            return RepaintBoundary(
                              child: Center(
                                child: GlassContainer(
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        Icons.cloud_off,
                                        size: 48,
                                        color: glassTheme.onSurfaceColor,
                                        semanticLabel: 'Connection error',
                                      ),
                                      const SizedBox(height: 16),
                                      Text(
                                        'Connection Error',
                                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                          color: glassTheme.onSurfaceColor,
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        'Trying to reconnect...',
                                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                          color: glassTheme.onSurfaceSecondaryColor,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          }

                          final hr = data['heart_rate']?.toString() ?? '--';
                          final act = _describeActivity(data['activity_level']);
                          final loc = _describeLocation(data['location']);
                          
                          if (_lastUpdated == null) {
                            _lastUpdated = DateTime.now();
                          }

                          return Column(
                            children: [
                              const SizedBox(height: 8),
                              if (_lastUpdated != null)
                                Align(
                                  alignment: Alignment.centerLeft,
                                  child: Semantics(
                                    label: 'Last updated ${_formatTimestamp(_lastUpdated!.toIso8601String())}',
                                    child: Text(
                                      'Last updated: ${_formatTimestamp(_lastUpdated!.toIso8601String())}',
                                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                        color: glassTheme.onSurfaceSecondaryColor,
                                      ),
                                    ),
                                  ),
                                ),
                              const SizedBox(height: 16),
                              RepaintBoundary(child: GlassContainer(child: _Metric(label: 'Heart Rate', value: '$hr BPM', icon: Icons.favorite))),
                              const SizedBox(height: 12),
                              RepaintBoundary(child: GlassContainer(child: _Metric(label: 'Activity', value: act, icon: Icons.directions_run))),
                              const SizedBox(height: 12),
                              RepaintBoundary(child: GlassContainer(child: _Metric(label: 'Location', value: loc, icon: Icons.location_on_outlined))),
                              const SizedBox(height: 16),
                              Align(
                                alignment: Alignment.centerLeft,
                                child: Text(
                                  "Today's Story",
                                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                    color: glassTheme.onSurfaceColor,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                              const SizedBox(height: 8),
                              Expanded(
                                child: timelineAsync.when(
                                  data: (timeline) => RepaintBoundary(
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
                                          child: RepaintBoundary(
                                            child: GlassContainer(
                                              child: Row(
                                                children: [
                                                  Expanded(
                                                    child: Text(
                                                      '${_formatTimestamp(ts)} — $label',
                                                      style: TextStyle(color: glassTheme.onSurfaceColor),
                                                    ),
                                                  ),
                                                  FeedbackButton(
                                                    icon: Icons.thumb_up,
                                                    feedbackType: 'positive',
                                                    isSelected: acked,
                                                    selectedColor: Colors.greenAccent,
                                                    unselectedColor: glassTheme.onSurfaceSecondaryColor,
                                                    onPressed: () async {
                                                      try {
                                                        await _service.submitFeedback(id, 'correct');
                                                        if (mounted) {
                                                          setState(() => _ack.add(id));
                                                        }
                                                      } catch (e) {
                                                        // Handle error silently or show snackbar
                                                        if (mounted && context.mounted) {
                                                          ScaffoldMessenger.of(context).showSnackBar(
                                                            const SnackBar(content: Text('Failed to submit feedback')),
                                                          );
                                                        }
                                                      }
                                                    },
                                                  ),
                                                  const SizedBox(width: 8),
                                                  FeedbackButton(
                                                    icon: Icons.thumb_down,
                                                    feedbackType: 'negative',
                                                    isSelected: acked,
                                                    selectedColor: Colors.redAccent,
                                                    unselectedColor: glassTheme.onSurfaceSecondaryColor,
                                                    onPressed: () async {
                                                      try {
                                                        await _service.submitFeedback(id, 'incorrect');
                                                        if (mounted) {
                                                          setState(() => _ack.add(id));
                                                        }
                                                      } catch (e) {
                                                        // Handle error silently or show snackbar
                                                        if (mounted && context.mounted) {
                                                          ScaffoldMessenger.of(context).showSnackBar(
                                                            const SnackBar(content: Text('Failed to submit feedback')),
                                                          );
                                                        }
                                                      }
                                                    },
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ),
                                        );
                                      },
                                    ),
                                  ),
                                  loading: () => RepaintBoundary(
                                    child: Center(
                                      child: GlassContainer(
                                        child: Column(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            CircularProgressIndicator(color: glassTheme.primaryAccent),
                                            const SizedBox(height: 16),
                                            Text(
                                              'Loading timeline...',
                                              style: TextStyle(color: glassTheme.onSurfaceColor),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                  error: (e, _) => RepaintBoundary(
                                    child: Center(
                                      child: GlassContainer(
                                        child: Column(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(
                                              Icons.error,
                                              color: Colors.redAccent,
                                              size: 48,
                                              semanticLabel: 'Timeline error',
                                            ),
                                            const SizedBox(height: 16),
                                            Text(
                                              'Timeline Error',
                                              style: TextStyle(color: glassTheme.onSurfaceColor),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          );
                        },
                        loading: () => RepaintBoundary(
                          child: Center(
                            child: GlassContainer(
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  CircularProgressIndicator(color: glassTheme.primaryAccent),
                                  const SizedBox(height: 16),
                                  Text(
                                    'Loading dashboard...',
                                    style: TextStyle(color: glassTheme.onSurfaceColor),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        error: (e, _) => RepaintBoundary(
                          child: Center(
                            child: GlassContainer(
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.error,
                                    color: Colors.redAccent,
                                    size: 48,
                                    semanticLabel: 'Dashboard error',
                                  ),
                                  const SizedBox(height: 16),
                                  Text(
                                    'Dashboard Error',
                                    style: TextStyle(color: glassTheme.onSurfaceColor),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
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

  static final _pollingService = AdaptivePollingService(baseUrl: _apiBaseUrl);

  static final _realTimeProvider = StreamProvider.autoDispose<Map<String, dynamic>>((ref) async* {
    // Use offline cache while loading
    final cachedData = await OfflineCacheService.retrieve(
      CacheKeys.realTimeData,
      maxAge: const Duration(minutes: 5),
    );
    
    if (cachedData != null) {
      yield cachedData;
    }
    
    // Start adaptive polling stream
    final pollingStream = _pollingService.createPollingStream('/realtime?collar_id=$_collarId');
    
    await for (final data in pollingStream) {
      // Cache successful responses
      if (!data.containsKey('error')) {
        await OfflineCacheService.store(CacheKeys.realTimeData, data);
      }
      yield data;
    }
  });

  static final _timelineProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
    // Try cache first
    final cachedData = await OfflineCacheService.retrieve(
      CacheKeys.petTimeline,
      maxAge: const Duration(hours: 1),
    );
    
    if (cachedData != null && cachedData.containsKey('timeline')) {
      return cachedData['timeline'] as List<dynamic>;
    }
    
    // Fetch fresh data
    final service = APIService(baseUrl: _apiBaseUrl);
    final timeline = await service.getPetTimeline(_collarId);
    
    // Cache the result
    await OfflineCacheService.store(CacheKeys.petTimeline, {'timeline': timeline});
    
    return timeline;
  });
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value, required this.icon});
  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final glassTheme = context.glassTheme;
    
    return Row(
      children: [
        Icon(icon, color: glassTheme.onSurfaceColor, size: 28),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: glassTheme.onSurfaceSecondaryColor,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: glassTheme.onSurfaceColor,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}