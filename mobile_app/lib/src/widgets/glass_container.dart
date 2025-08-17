import 'dart:ui';
import 'package:flutter/material.dart';

/// A glass morphism container widget that applies a blur effect with customizable
/// opacity and border styling.
///
/// This widget creates a glassmorphism effect by combining a [BackdropFilter]
/// with a semi-transparent container. The appearance can be customized through
/// the [opacity] and [borderAlpha] parameters.
class GlassContainer extends StatelessWidget {
  /// The child widget to display inside the glass container.
  final Widget child;
  
  /// The padding to apply inside the container. Defaults to 16dp on all sides.
  final EdgeInsets padding;
  
  /// The border radius for the container corners. Defaults to 20dp.
  final double radius;
  
  /// The opacity of the container background. Should be between 0.0 and 1.0.
  /// Defaults to 0.12 for a subtle glass effect.
  final double opacity;
  
  /// The opacity of the container border. Should be between 0.0 and 1.0.
  /// Defaults to 0.2 for a subtle border effect.
  final double borderAlpha;
  
  const GlassContainer({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.radius = 20,
    this.opacity = 0.12,
    this.borderAlpha = 0.2,
  }) : assert(opacity >= 0.0 && opacity <= 1.0, 'opacity must be between 0.0 and 1.0'),
       assert(borderAlpha >= 0.0 && borderAlpha <= 1.0, 'borderAlpha must be between 0.0 and 1.0'),
       assert(radius >= 0.0, 'radius must be non-negative');

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(opacity),
            borderRadius: BorderRadius.circular(radius),
            border: Border.all(color: Colors.white.withOpacity(borderAlpha), width: 1),
          ),
          child: child,
        ),
      ),
    );
  }
}
