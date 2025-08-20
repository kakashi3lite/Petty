import 'dart:ui';
import 'package:flutter/material.dart';

class GlassContainer extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final double opacity;
  final double borderAlpha;
  
  const GlassContainer({
    super.key, 
    required this.child, 
    this.padding = const EdgeInsets.all(16), 
    this.radius = 20,
    this.opacity = 0.12,
    this.borderAlpha = 0.2,
  });

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
