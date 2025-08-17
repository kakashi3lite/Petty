import 'package:flutter/material.dart';
import 'glass_tokens.dart';

/// Material 3 theme configuration with glassmorphism support
class AppTheme {
  AppTheme._();

  // Light theme with glassmorphism
  static ThemeData light() {
    const primaryColor = Color(0xFF6dd5ed);
    const surfaceColor = Color(0xFFFFFBFE);
    
    final colorScheme = ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.light,
      surface: surfaceColor,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      // Ensure text has proper contrast over glass surfaces
      textTheme: const TextTheme(
        headlineMedium: TextStyle(
          fontWeight: FontWeight.bold,
          color: Colors.black87, // High contrast
        ),
        titleLarge: TextStyle(
          fontWeight: FontWeight.w600,
          color: Colors.black87,
        ),
        titleMedium: TextStyle(
          fontWeight: FontWeight.w500,
          color: Colors.black87,
        ),
        bodyLarge: TextStyle(
          color: Colors.black87,
        ),
        bodyMedium: TextStyle(
          color: Colors.black87,
        ),
      ),
      // Ensure touch targets meet a11y requirements (≥48dp)
      materialTapTargetSize: MaterialTapTargetSize.standard,
      visualDensity: VisualDensity.standard,
      extensions: const [
        GlassTokens.light,
      ],
    );
  }

  // Dark theme with glassmorphism
  static ThemeData dark() {
    const primaryColor = Color(0xFF6dd5ed);
    const surfaceColor = Color(0xFF1C1B1F);
    
    final colorScheme = ColorScheme.fromSeed(
      seedColor: primaryColor,
      brightness: Brightness.dark,
      surface: surfaceColor,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      // High contrast text for glass surfaces in dark mode
      textTheme: const TextTheme(
        headlineMedium: TextStyle(
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
        titleLarge: TextStyle(
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
        titleMedium: TextStyle(
          fontWeight: FontWeight.w500,
          color: Colors.white70, // Slightly reduced for hierarchy
        ),
        bodyLarge: TextStyle(
          color: Colors.white,
        ),
        bodyMedium: TextStyle(
          color: Colors.white,
        ),
      ),
      // Ensure touch targets meet a11y requirements (≥48dp)
      materialTapTargetSize: MaterialTapTargetSize.standard,
      visualDensity: VisualDensity.standard,
      extensions: const [
        GlassTokens.dark,
      ],
    );
  }
}

/// Theme mode provider for dark mode toggle
class ThemeModeProvider extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;

  ThemeMode get themeMode => _themeMode;

  void setThemeMode(ThemeMode mode) {
    _themeMode = mode;
    notifyListeners();
  }

  void toggleTheme() {
    _themeMode = _themeMode == ThemeMode.light 
        ? ThemeMode.dark 
        : ThemeMode.light;
    notifyListeners();
  }
}