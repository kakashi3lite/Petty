import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../services/adaptive_polling_service.dart';

/// Provider for API service
final apiServiceProvider = Provider<APIService>((ref) {
  return APIService(baseUrl: 'https://api.example.com');
});

/// Provider for collar ID
final collarIdProvider = Provider<String>((ref) => 'SN-123');

/// Adaptive polling provider for real-time data
final adaptiveRealTimeProvider = StreamProvider.autoDispose<Map<String, dynamic>>((ref) {
  final controller = StreamController<Map<String, dynamic>>();
  final apiService = ref.watch(apiServiceProvider);
  final collarId = ref.watch(collarIdProvider);
  
  // Create adaptive polling service
  final pollingService = AdaptivePollingService<Map<String, dynamic>>(
    pollFunction: () => apiService.getRealTimeData(collarId),
    onData: (data) {
      if (!controller.isClosed) {
        controller.add(data);
      }
    },
    onError: (error) {
      if (!controller.isClosed) {
        controller.add({"error": error.toString()});
      }
    },
  );
  
  // Start polling when provider is listened to
  pollingService.start();
  
  // Cleanup when provider is disposed
  ref.onDispose(() {
    pollingService.stop();
    if (!controller.isClosed) {
      controller.close();
    }
  });
  
  return controller.stream;
});

/// Timeline provider (unchanged for now)
final timelineProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final apiService = ref.watch(apiServiceProvider);
  final collarId = ref.watch(collarIdProvider);
  return apiService.getPetTimeline(collarId);
});

/// Provider for tracking last update time
final lastUpdateProvider = StateProvider<DateTime?>((ref) => null);

/// Provider for connection status
final connectionStatusProvider = StateProvider<ConnectionStatus>((ref) => ConnectionStatus.connecting);

enum ConnectionStatus {
  connecting,
  connected,
  error,
  disconnected,
}