import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'features/dashboard/presentation/dashboard_screen.dart';
import 'features/pet_profile/presentation/pet_profile_screen.dart';
import 'features/tele_vet/presentation/tele_vet_screen.dart';
import 'theme/petty_theme.dart';

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
      ],
    );

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      theme: PettyTheme.lightTheme(),
      darkTheme: PettyTheme.darkTheme(),
      themeMode: ThemeMode.system, // Respects system theme preference
      routerConfig: router,
    );
  }
}
