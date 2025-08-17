import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/adaptive_poll_controller.dart';
import '../services/api_service.dart';

/// Provider for the adaptive poll controller
final adaptivePollControllerProvider = Provider<AdaptivePollController>((ref) {
  final controller = AdaptivePollController();
  ref.onDispose(() {
    controller.dispose();
  });
  return controller;
});

/// Provider for real-time data using adaptive polling
final adaptiveRealTimeProvider = StreamProvider.family.autoDispose<Map<String, dynamic>, String>(
  (ref, collarId) async* {
    const String apiBaseUrl = 'https://api.example.com';
    final service = APIService(baseUrl: apiBaseUrl);
    final controller = ref.watch(adaptivePollControllerProvider);
    
    // Start adaptive polling
    controller.start();
    
    // Listen to poll ticks and fetch data
    await for (final _ in controller.stream) {
      try {
        final data = await service.getRealTimeData(collarId);
        controller.onRequestSuccess();
        yield data;
      } catch (e) {
        controller.onRequestFailure();
        yield {"error": e.toString()};
      }
    }
  },
);