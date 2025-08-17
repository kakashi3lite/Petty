import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme/glass_tokens.dart';

/// High-performance glassmorphism container using ImageFiltered
/// Follows Flutter best practices: uses ImageFiltered for contained blur,
/// bounded with ClipRRect to avoid overdraw, optimized for scrolling lists
class GlassContainer extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final double? elevation;

  const GlassContainer({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.radius = 20,
    this.elevation,
  });

  @override
  Widget build(BuildContext context) {
    final glassTokens = context.glassTokens;
    final effectiveElevation = elevation ?? glassTokens.elevation;

    return RepaintBoundary(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: ImageFiltered(
          imageFilter: ImageFilter.blur(
            sigmaX: glassTokens.blurSigma,
            sigmaY: glassTokens.blurSigma,
          ),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              // Glass tint with proper opacity for contrast compliance
              color: glassTokens.tintColor.withOpacity(glassTokens.tintOpacity),
              borderRadius: BorderRadius.circular(radius),
              border: Border.all(
                color: glassTokens.borderColor.withOpacity(glassTokens.borderOpacity),
                width: glassTokens.borderWidth,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: effectiveElevation,
                  offset: Offset(0, effectiveElevation / 2),
                ),
              ],
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}
