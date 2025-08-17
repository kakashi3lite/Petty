import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'src/app.dart';
import 'src/services/offline_cache_service.dart';
import 'src/services/telemetry_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize services
  await OfflineCacheService.initialize();
  await TelemetryService.initialize();
  await RemoteConfigService.initialize();
  
  runApp(const ProviderScope(child: PettyApp()));
}
