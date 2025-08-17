import 'dart:ui';
import 'package:flutter/material.dart';

/// Glassmorphism design tokens following Material 3 ThemeExtension pattern
@immutable
class GlassTokens extends ThemeExtension<GlassTokens> {
  const GlassTokens({
    required this.blurSigma,
    required this.tintColor,
    required this.tintOpacity,
    required this.borderColor,
    required this.borderOpacity,
    required this.borderWidth,
    required this.elevation,
  });

  final double blurSigma;
  final Color tintColor;
  final double tintOpacity;
  final Color borderColor;
  final double borderOpacity;
  final double borderWidth;
  final double elevation;

  // Light theme glass tokens
  static const light = GlassTokens(
    blurSigma: 12.0,
    tintColor: Colors.white,
    tintOpacity: 0.12,
    borderColor: Colors.white,
    borderOpacity: 0.2,
    borderWidth: 1.0,
    elevation: 4.0,
  );

  // Dark theme glass tokens
  static const dark = GlassTokens(
    blurSigma: 14.0,
    tintColor: Colors.white,
    tintOpacity: 0.08,
    borderColor: Colors.white,
    borderOpacity: 0.15,
    borderWidth: 1.0,
    elevation: 6.0,
  );

  @override
  GlassTokens copyWith({
    double? blurSigma,
    Color? tintColor,
    double? tintOpacity,
    Color? borderColor,
    double? borderOpacity,
    double? borderWidth,
    double? elevation,
  }) {
    return GlassTokens(
      blurSigma: blurSigma ?? this.blurSigma,
      tintColor: tintColor ?? this.tintColor,
      tintOpacity: tintOpacity ?? this.tintOpacity,
      borderColor: borderColor ?? this.borderColor,
      borderOpacity: borderOpacity ?? this.borderOpacity,
      borderWidth: borderWidth ?? this.borderWidth,
      elevation: elevation ?? this.elevation,
    );
  }

  @override
  GlassTokens lerp(ThemeExtension<GlassTokens>? other, double t) {
    if (other is! GlassTokens) {
      return this;
    }
    return GlassTokens(
      blurSigma: lerpDouble(blurSigma, other.blurSigma, t) ?? blurSigma,
      tintColor: Color.lerp(tintColor, other.tintColor, t) ?? tintColor,
      tintOpacity: lerpDouble(tintOpacity, other.tintOpacity, t) ?? tintOpacity,
      borderColor: Color.lerp(borderColor, other.borderColor, t) ?? borderColor,
      borderOpacity: lerpDouble(borderOpacity, other.borderOpacity, t) ?? borderOpacity,
      borderWidth: lerpDouble(borderWidth, other.borderWidth, t) ?? borderWidth,
      elevation: lerpDouble(elevation, other.elevation, t) ?? elevation,
    );
  }
}

/// Helper extension to access glass tokens from BuildContext
extension GlassTokensExtension on BuildContext {
  GlassTokens get glassTokens => Theme.of(this).extension<GlassTokens>() ?? GlassTokens.light;
}