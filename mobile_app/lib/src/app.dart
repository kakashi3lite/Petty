import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:dynamic_color/dynamic_color.dart';
import 'features/dashboard/presentation/dashboard_screen.dart';
import 'features/pet_profile/presentation/pet_profile_screen.dart';
import 'features/tele_vet/presentation/tele_vet_screen.dart';
import 'theme/glassmorphism_theme.dart';

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

    return DynamicColorBuilder(
      builder: (ColorScheme? lightDynamic, ColorScheme? darkDynamic) {
        // Generate color schemes with Material 3 from seed color
        final seedColor = const Color(0xFF6dd5ed);
        
        final lightColorScheme = lightDynamic ?? ColorScheme.fromSeed(
          seedColor: seedColor,
          brightness: Brightness.light,
        );
        
        final darkColorScheme = darkDynamic ?? ColorScheme.fromSeed(
          seedColor: seedColor,
          brightness: Brightness.dark,
        );

        final lightTheme = ThemeData(
          useMaterial3: true,
          colorScheme: lightColorScheme,
          extensions: const [GlassmorphismTheme.light],
          textTheme: const TextTheme(
            headlineMedium: TextStyle(fontWeight: FontWeight.bold),
          ),
        );

        final darkTheme = ThemeData(
          useMaterial3: true,
          colorScheme: darkColorScheme,
          extensions: const [GlassmorphismTheme.dark],
          textTheme: const TextTheme(
            headlineMedium: TextStyle(fontWeight: FontWeight.bold),
          ),
        );

        return MaterialApp.router(
          debugShowCheckedModeBanner: false,
          title: 'Petty',
          theme: lightTheme,
          darkTheme: darkTheme,
          themeMode: ThemeMode.system, // Respect system theme preference
          routerConfig: router,
        );
      },
    );
  }
}
