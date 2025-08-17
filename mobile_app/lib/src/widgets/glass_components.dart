import 'package:flutter/material.dart';
import '../theme/glass_tokens.dart';
import 'glass_container.dart';

/// High-performance glass card component
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final VoidCallback? onTap;
  final double? elevation;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.radius = 16,
    this.onTap,
    this.elevation,
  });

  @override
  Widget build(BuildContext context) {
    Widget card = GlassContainer(
      padding: padding,
      radius: radius,
      elevation: elevation,
      child: child,
    );

    if (onTap != null) {
      card = InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(radius),
        child: card,
      );
    }

    return card;
  }
}

/// Glass app bar with proper elevation and blur
class GlassAppBar extends StatelessWidget implements PreferredSizeWidget {
  final Widget title;
  final List<Widget>? actions;
  final Widget? leading;
  final bool centerTitle;
  final double elevation;

  const GlassAppBar({
    super.key,
    required this.title,
    this.actions,
    this.leading,
    this.centerTitle = true,
    this.elevation = 8.0,
  });

  @override
  Widget build(BuildContext context) {
    final glassTokens = context.glassTokens;
    
    return PreferredSize(
      preferredSize: preferredSize,
      child: SafeArea(
        child: GlassContainer(
          radius: 0,
          elevation: elevation,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            title: title,
            actions: actions,
            leading: leading,
            centerTitle: centerTitle,
          ),
        ),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight + 8);
}

/// Glass navigation bar for bottom navigation
class GlassNavBar extends StatelessWidget {
  final List<GlassNavItem> items;
  final int currentIndex;
  final ValueChanged<int>? onTap;
  final double elevation;

  const GlassNavBar({
    super.key,
    required this.items,
    this.currentIndex = 0,
    this.onTap,
    this.elevation = 12.0,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      child: GlassContainer(
        radius: 24,
        elevation: elevation,
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: items.asMap().entries.map((entry) {
            final index = entry.key;
            final item = entry.value;
            final isSelected = index == currentIndex;
            
            return GestureDetector(
              onTap: () => onTap?.call(index),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  color: isSelected 
                      ? Theme.of(context).colorScheme.primary.withOpacity(0.2)
                      : Colors.transparent,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      item.icon,
                      color: isSelected 
                          ? Theme.of(context).colorScheme.primary
                          : Colors.white70,
                      size: 24,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      item.label,
                      style: TextStyle(
                        color: isSelected 
                            ? Theme.of(context).colorScheme.primary
                            : Colors.white70,
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }
}

/// Navigation item for GlassNavBar
class GlassNavItem {
  final IconData icon;
  final String label;

  const GlassNavItem({
    required this.icon,
    required this.label,
  });
}

/// Glass modal sheet for overlays
class GlassSheet extends StatelessWidget {
  final Widget child;
  final double? height;
  final EdgeInsets padding;
  final double radius;

  const GlassSheet({
    super.key,
    required this.child,
    this.height,
    this.padding = const EdgeInsets.all(24),
    this.radius = 24,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      width: double.infinity,
      margin: const EdgeInsets.all(16),
      child: GlassContainer(
        radius: radius,
        elevation: 16,
        padding: padding,
        child: child,
      ),
    );
  }

  /// Show glass modal bottom sheet
  static Future<T?> show<T>({
    required BuildContext context,
    required Widget child,
    double? height,
    EdgeInsets padding = const EdgeInsets.all(24),
    double radius = 24,
  }) {
    return showModalBottomSheet<T>(
      context: context,
      backgroundColor: Colors.transparent,
      elevation: 0,
      builder: (context) => GlassSheet(
        height: height,
        padding: padding,
        radius: radius,
        child: child,
      ),
    );
  }
}