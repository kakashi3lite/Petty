import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'features/dashboard/presentation/dashboard_screen.dart';
import 'features/pet_profile/presentation/pet_profile_screen.dart';
import 'features/tele_vet/presentation/tele_vet_screen.dart';
import 'features/gallery/presentation/component_gallery_screen.dart';
import 'theme/app_theme.dart';

class PettyApp extends StatelessWidget {
  const PettyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final router = GoRouter(
      initialLocation: "/",
      routes: [
        GoRoute(path: "/", builder: (_, __) => const DashboardScreen()),
        GoRoute(path: "/profile", builder: (_, __) => const PetProfileScreen()),
        GoRoute(path: "/tele-vet", builder: (_, __) => const TeleVetScreen()),
        GoRoute(path: "/gallery", builder: (_, __) => const ComponentGalleryScreen()),
      ],
    );

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Petty - Smart Pet Care',
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: ThemeMode.system, // Respects system preference
      routerConfig: router,
    );
  }
}
