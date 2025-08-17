import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme/glassmorphism_theme.dart';

class GlassContainer extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final double? radius;
  final Color? surfaceColor;
  final Color? borderColor;
  final double? blurSigma;
  
  const GlassContainer({
    super.key, 
    required this.child, 
    this.padding = const EdgeInsets.all(16), 
    this.radius,
    this.surfaceColor,
    this.borderColor,
    this.blurSigma,
  });

  @override
  Widget build(BuildContext context) {
    final glassTheme = context.glassTheme;
    final effectiveRadius = radius ?? glassTheme.defaultRadius;
    final effectiveSurfaceColor = surfaceColor ?? glassTheme.surfaceColor;
    final effectiveBorderColor = borderColor ?? glassTheme.borderColor;
    final effectiveBlurSigma = blurSigma ?? glassTheme.blurSigma;
    
    return RepaintBoundary(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(effectiveRadius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: effectiveBlurSigma, sigmaY: effectiveBlurSigma),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: effectiveSurfaceColor,
              borderRadius: BorderRadius.circular(effectiveRadius),
              border: Border.all(color: effectiveBorderColor, width: glassTheme.borderWidth),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}
