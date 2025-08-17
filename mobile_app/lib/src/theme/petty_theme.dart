import 'package:flutter/material.dart';

/// Material 3 theme configuration with glassmorphism integration
/// and accessibility compliance
class PettyTheme {
  // Color palette following Material 3 guidelines
  static const Color _primarySeed = Color(0xFF6dd5ed);
  static const Color _secondarySeed = Color(0xFF2196f3);
  
  // Custom colors for glassmorphism
  static const Color _glassOverlay = Color(0x1FFFFFFF);
  static const Color _glassBorder = Color(0x33FFFFFF);
  
  /// Light theme configuration
  static ThemeData lightTheme() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: _primarySeed,
      brightness: Brightness.light,
    );
    
    return _buildTheme(colorScheme);
  }
  
  /// Dark theme configuration with enhanced contrast for accessibility
  static ThemeData darkTheme() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: _primarySeed,
      brightness: Brightness.dark,
    ).copyWith(
      // Enhanced contrast ratios for accessibility (≥4.5:1)
      onSurface: const Color(0xFFE8E8E8), // Increased contrast
      onSurfaceVariant: const Color(0xFFD0D0D0),
      outline: const Color(0xFF8A8A8A),
    );
    
    return _buildTheme(colorScheme);
  }
  
  /// Build theme with common configuration
  static ThemeData _buildTheme(ColorScheme colorScheme) {
    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      
      // Typography with accessibility considerations
      textTheme: _buildTextTheme(colorScheme),
      
      // Component themes
      appBarTheme: _buildAppBarTheme(colorScheme),
      elevatedButtonTheme: _buildElevatedButtonTheme(colorScheme),
      filledButtonTheme: _buildFilledButtonTheme(colorScheme),
      cardTheme: _buildCardTheme(colorScheme),
      bottomNavigationBarTheme: _buildBottomNavigationBarTheme(colorScheme),
      floatingActionButtonTheme: _buildFABTheme(colorScheme),
      
      // Accessibility enhancements
      visualDensity: VisualDensity.adaptivePlatformDensity,
      materialTapTargetSize: MaterialTapTargetSize.padded, // Ensures 44x44 minimum
    );
  }
  
  /// Text theme with proper contrast and sizing
  static TextTheme _buildTextTheme(ColorScheme colorScheme) {
    return TextTheme(
      displayLarge: TextStyle(
        fontSize: 32,
        fontWeight: FontWeight.w400,
        color: colorScheme.onSurface,
        height: 1.2,
      ),
      headlineLarge: TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.w600,
        color: colorScheme.onSurface,
        height: 1.25,
      ),
      headlineMedium: TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.w600,
        color: colorScheme.onSurface,
        height: 1.3,
      ),
      headlineSmall: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: colorScheme.onSurface,
        height: 1.3,
      ),
      titleLarge: TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w500,
        color: colorScheme.onSurface,
        height: 1.4,
      ),
      titleMedium: TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w500,
        color: colorScheme.onSurface,
        height: 1.4,
      ),
      bodyLarge: TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w400,
        color: colorScheme.onSurface,
        height: 1.5,
      ),
      bodyMedium: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w400,
        color: colorScheme.onSurface,
        height: 1.5,
      ),
      labelLarge: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w500,
        color: colorScheme.onSurface,
        height: 1.4,
      ),
    );
  }
  
  /// App bar theme with glassmorphism support
  static AppBarTheme _buildAppBarTheme(ColorScheme colorScheme) {
    return AppBarTheme(
      backgroundColor: colorScheme.surface.withOpacity(0.8),
      foregroundColor: colorScheme.onSurface,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
      titleTextStyle: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: colorScheme.onSurface,
      ),
    );
  }
  
  /// Elevated button theme with accessibility
  static ElevatedButtonThemeData _buildElevatedButtonTheme(ColorScheme colorScheme) {
    return ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: colorScheme.primaryContainer.withOpacity(0.8),
        foregroundColor: colorScheme.onPrimaryContainer,
        minimumSize: const Size(44, 44), // Accessibility: minimum touch target
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        elevation: 0,
      ),
    );
  }
  
  /// Filled button theme
  static FilledButtonThemeData _buildFilledButtonTheme(ColorScheme colorScheme) {
    return FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: colorScheme.primary,
        foregroundColor: colorScheme.onPrimary,
        minimumSize: const Size(44, 44),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
  
  /// Card theme with glassmorphism
  static CardTheme _buildCardTheme(ColorScheme colorScheme) {
    return CardTheme(
      color: colorScheme.surface.withOpacity(0.9),
      surfaceTintColor: colorScheme.surfaceTint.withOpacity(0.1),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: colorScheme.outline.withOpacity(0.2),
          width: 1,
        ),
      ),
    );
  }
  
  /// Bottom navigation bar theme
  static BottomNavigationBarThemeData _buildBottomNavigationBarTheme(ColorScheme colorScheme) {
    return BottomNavigationBarThemeData(
      backgroundColor: colorScheme.surface.withOpacity(0.9),
      selectedItemColor: colorScheme.primary,
      unselectedItemColor: colorScheme.onSurface.withOpacity(0.6),
      elevation: 8,
      type: BottomNavigationBarType.fixed,
      selectedLabelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      unselectedLabelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w400),
    );
  }
  
  /// Floating action button theme
  static FloatingActionButtonThemeData _buildFABTheme(ColorScheme colorScheme) {
    return FloatingActionButtonThemeData(
      backgroundColor: colorScheme.primaryContainer.withOpacity(0.9),
      foregroundColor: colorScheme.onPrimaryContainer,
      elevation: 6,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    );
  }
  
  /// Glass overlay colors for glassmorphism components
  static Color glassOverlay(ColorScheme colorScheme) {
    return colorScheme.brightness == Brightness.dark
        ? const Color(0x1FFFFFFF)
        : const Color(0x1F000000);
  }
  
  /// Glass border colors
  static Color glassBorder(ColorScheme colorScheme) {
    return colorScheme.brightness == Brightness.dark
        ? const Color(0x33FFFFFF)
        : const Color(0x33000000);
  }
  
  /// Accessibility helpers
  static bool hasMinimumContrast(Color foreground, Color background) {
    // Simple contrast ratio calculation
    final foregroundLuminance = foreground.computeLuminance();
    final backgroundLuminance = background.computeLuminance();
    
    final lighter = foregroundLuminance > backgroundLuminance
        ? foregroundLuminance
        : backgroundLuminance;
    final darker = foregroundLuminance > backgroundLuminance
        ? backgroundLuminance
        : foregroundLuminance;
    
    final contrast = (lighter + 0.05) / (darker + 0.05);
    return contrast >= 4.5; // WCAG AA standard
  }
  
  /// Check if touch target meets minimum size
  static bool hasMinimumTouchTarget(Size size) {
    return size.width >= 44.0 && size.height >= 44.0;
  }
}