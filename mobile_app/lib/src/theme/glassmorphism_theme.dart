import 'dart:ui';
import 'package:flutter/material.dart';

/// Glassmorphism design system extension for consistent theming
@immutable
class GlassmorphismTheme extends ThemeExtension<GlassmorphismTheme> {
  final Color surfaceColor;
  final Color borderColor;
  final double blurSigma;
  final double borderWidth;
  final double defaultRadius;
  final Color overlayColor;
  final Color primaryAccent;
  final Color secondaryAccent;
  final Color onSurfaceColor;
  final Color onSurfaceSecondaryColor;
  
  const GlassmorphismTheme({
    required this.surfaceColor,
    required this.borderColor,
    required this.blurSigma,
    required this.borderWidth,
    required this.defaultRadius,
    required this.overlayColor,
    required this.primaryAccent,
    required this.secondaryAccent,
    required this.onSurfaceColor,
    required this.onSurfaceSecondaryColor,
  });
  
  /// Light theme glassmorphism
  static const GlassmorphismTheme light = GlassmorphismTheme(
    surfaceColor: Color(0x26FFFFFF), // 15% white
    borderColor: Color(0x33FFFFFF), // 20% white
    blurSigma: 12.0,
    borderWidth: 1.0,
    defaultRadius: 16.0,
    overlayColor: Color(0x0AFFFFFF), // 4% white overlay
    primaryAccent: Color(0xFF6dd5ed),
    secondaryAccent: Color(0xFF2193b0),
    onSurfaceColor: Color(0xFF1A1A1A), // AA compliant on glass
    onSurfaceSecondaryColor: Color(0xFF616161), // AA compliant secondary
  );
  
  /// Dark theme glassmorphism
  static const GlassmorphismTheme dark = GlassmorphismTheme(
    surfaceColor: Color(0x26FFFFFF), // 15% white
    borderColor: Color(0x33FFFFFF), // 20% white
    blurSigma: 14.0,
    borderWidth: 1.0,
    defaultRadius: 20.0,
    overlayColor: Color(0x0DFFFFFF), // 5% white overlay
    primaryAccent: Color(0xFF6dd5ed),
    secondaryAccent: Color(0xFF2193b0),
    onSurfaceColor: Color(0xFFFFFFFF), // White text on dark glass
    onSurfaceSecondaryColor: Color(0xFFE0E0E0), // AA compliant secondary
  );
  
  @override
  GlassmorphismTheme copyWith({
    Color? surfaceColor,
    Color? borderColor,
    double? blurSigma,
    double? borderWidth,
    double? defaultRadius,
    Color? overlayColor,
    Color? primaryAccent,
    Color? secondaryAccent,
    Color? onSurfaceColor,
    Color? onSurfaceSecondaryColor,
  }) {
    return GlassmorphismTheme(
      surfaceColor: surfaceColor ?? this.surfaceColor,
      borderColor: borderColor ?? this.borderColor,
      blurSigma: blurSigma ?? this.blurSigma,
      borderWidth: borderWidth ?? this.borderWidth,
      defaultRadius: defaultRadius ?? this.defaultRadius,
      overlayColor: overlayColor ?? this.overlayColor,
      primaryAccent: primaryAccent ?? this.primaryAccent,
      secondaryAccent: secondaryAccent ?? this.secondaryAccent,
      onSurfaceColor: onSurfaceColor ?? this.onSurfaceColor,
      onSurfaceSecondaryColor: onSurfaceSecondaryColor ?? this.onSurfaceSecondaryColor,
    );
  }
  
  @override
  GlassmorphismTheme lerp(ThemeExtension<GlassmorphismTheme>? other, double t) {
    if (other is! GlassmorphismTheme) {
      return this;
    }
    
    return GlassmorphismTheme(
      surfaceColor: Color.lerp(surfaceColor, other.surfaceColor, t)!,
      borderColor: Color.lerp(borderColor, other.borderColor, t)!,
      blurSigma: lerpDouble(blurSigma, other.blurSigma, t)!,
      borderWidth: lerpDouble(borderWidth, other.borderWidth, t)!,
      defaultRadius: lerpDouble(defaultRadius, other.defaultRadius, t)!,
      overlayColor: Color.lerp(overlayColor, other.overlayColor, t)!,
      primaryAccent: Color.lerp(primaryAccent, other.primaryAccent, t)!,
      secondaryAccent: Color.lerp(secondaryAccent, other.secondaryAccent, t)!,
      onSurfaceColor: Color.lerp(onSurfaceColor, other.onSurfaceColor, t)!,
      onSurfaceSecondaryColor: Color.lerp(onSurfaceSecondaryColor, other.onSurfaceSecondaryColor, t)!,
    );
  }
}

/// Extension to easily access glassmorphism theme from BuildContext
extension GlassmorphismThemeExtension on BuildContext {
  GlassmorphismTheme get glassTheme =>
      Theme.of(this).extension<GlassmorphismTheme>() ?? GlassmorphismTheme.dark;
}