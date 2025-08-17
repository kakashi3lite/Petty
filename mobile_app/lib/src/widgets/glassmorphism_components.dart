import 'dart:ui';
import 'package:flutter/material.dart';

/// Glassmorphism design system components with Material 3 integration

/// Base glassmorphism card with elevation and accessibility support
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final double elevation;
  final VoidCallback? onTap;
  final String? semanticLabel;
  final Color? backgroundColor;
  final double blurStrength;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.radius = 16,
    this.elevation = 0,
    this.onTap,
    this.semanticLabel,
    this.backgroundColor,
    this.blurStrength = 10,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    
    Widget card = ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blurStrength, sigmaY: blurStrength),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: backgroundColor ?? colorScheme.surface.withOpacity(0.12),
            borderRadius: BorderRadius.circular(radius),
            border: Border.all(
              color: colorScheme.outline.withOpacity(0.2),
              width: 1,
            ),
          ),
          child: child,
        ),
      ),
    );

    if (elevation > 0) {
      card = Material(
        color: Colors.transparent,
        elevation: elevation,
        borderRadius: BorderRadius.circular(radius),
        child: card,
      );
    }

    if (onTap != null) {
      card = InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(radius),
        splashColor: colorScheme.primary.withOpacity(0.1),
        highlightColor: colorScheme.primary.withOpacity(0.05),
        child: card,
      );
    }

    if (semanticLabel != null) {
      card = Semantics(
        label: semanticLabel,
        button: onTap != null,
        child: card,
      );
    }

    return card;
  }
}

/// Glassmorphism app bar with proper accessibility
class GlassAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;
  final Widget? leading;
  final bool automaticallyImplyLeading;
  final double elevation;
  final Color? backgroundColor;
  final double blurStrength;

  const GlassAppBar({
    super.key,
    required this.title,
    this.actions,
    this.leading,
    this.automaticallyImplyLeading = true,
    this.elevation = 0,
    this.backgroundColor,
    this.blurStrength = 15,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blurStrength, sigmaY: blurStrength),
        child: AppBar(
          title: Text(
            title,
            style: theme.textTheme.headlineSmall?.copyWith(
              color: colorScheme.onSurface,
              fontWeight: FontWeight.w600,
            ),
          ),
          leading: leading,
          automaticallyImplyLeading: automaticallyImplyLeading,
          actions: actions,
          backgroundColor: backgroundColor ?? colorScheme.surface.withOpacity(0.8),
          elevation: elevation,
          surfaceTintColor: Colors.transparent,
          foregroundColor: colorScheme.onSurface,
        ),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}

/// Glassmorphism floating action button
class GlassFloatingActionButton extends StatelessWidget {
  final VoidCallback onPressed;
  final Widget child;
  final String? semanticLabel;
  final double elevation;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final double blurStrength;

  const GlassFloatingActionButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.semanticLabel,
    this.elevation = 6,
    this.backgroundColor,
    this.foregroundColor,
    this.blurStrength = 12,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return ClipOval(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blurStrength, sigmaY: blurStrength),
        child: FloatingActionButton(
          onPressed: onPressed,
          backgroundColor: backgroundColor ?? colorScheme.primaryContainer.withOpacity(0.8),
          foregroundColor: foregroundColor ?? colorScheme.onPrimaryContainer,
          elevation: elevation,
          child: Semantics(
            label: semanticLabel,
            button: true,
            child: child,
          ),
        ),
      ),
    );
  }
}

/// Glassmorphism bottom navigation bar
class GlassBottomNavigationBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final List<BottomNavigationBarItem> items;
  final double elevation;
  final Color? backgroundColor;
  final double blurStrength;

  const GlassBottomNavigationBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
    this.elevation = 8,
    this.backgroundColor,
    this.blurStrength = 15,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blurStrength, sigmaY: blurStrength),
        child: BottomNavigationBar(
          currentIndex: currentIndex,
          onTap: onTap,
          items: items,
          backgroundColor: backgroundColor ?? colorScheme.surface.withOpacity(0.9),
          selectedItemColor: colorScheme.primary,
          unselectedItemColor: colorScheme.onSurface.withOpacity(0.6),
          elevation: elevation,
          type: BottomNavigationBarType.fixed,
        ),
      ),
    );
  }
}

/// Glassmorphism button with accessibility features
class GlassButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final String? semanticLabel;
  final double blurStrength;
  final Size minimumSize;

  const GlassButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.padding = const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
    this.radius = 12,
    this.backgroundColor,
    this.foregroundColor,
    this.semanticLabel,
    this.blurStrength = 8,
    this.minimumSize = const Size(44, 44), // Accessibility: minimum touch target
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blurStrength, sigmaY: blurStrength),
        child: ElevatedButton(
          onPressed: onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: backgroundColor ?? colorScheme.primaryContainer.withOpacity(0.7),
            foregroundColor: foregroundColor ?? colorScheme.onPrimaryContainer,
            padding: padding,
            minimumSize: minimumSize,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(radius),
              side: BorderSide(
                color: colorScheme.outline.withOpacity(0.2),
                width: 1,
              ),
            ),
            elevation: 0,
          ),
          child: Semantics(
            label: semanticLabel,
            button: true,
            child: child,
          ),
        ),
      ),
    );
  }
}