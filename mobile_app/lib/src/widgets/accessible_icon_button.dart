import 'package:flutter/material.dart';

/// Accessible icon button that ensures ≥48dp touch targets
/// Meets WCAG AA accessibility guidelines
class AccessibleIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final Color? color;
  final String? tooltip;
  final String? semanticLabel;
  final double size;
  final double minTouchTargetSize;
  
  const AccessibleIconButton({
    super.key,
    required this.icon,
    required this.onPressed,
    this.color,
    this.tooltip,
    this.semanticLabel,
    this.size = 24.0,
    this.minTouchTargetSize = 48.0,
  });

  @override
  Widget build(BuildContext context) {
    Widget iconButton = IconButton(
      icon: Icon(icon, size: size),
      onPressed: onPressed,
      color: color,
      tooltip: tooltip,
      // Ensure minimum touch target size for accessibility
      constraints: BoxConstraints(
        minWidth: minTouchTargetSize,
        minHeight: minTouchTargetSize,
      ),
      style: IconButton.styleFrom(
        tapTargetSize: MaterialTapTargetSize.standard,
      ),
    );

    // Add semantic label if provided for screen readers
    if (semanticLabel != null) {
      iconButton = Semantics(
        label: semanticLabel,
        button: true,
        enabled: onPressed != null,
        child: iconButton,
      );
    }

    return iconButton;
  }
}

/// Feedback button specifically for timeline events
/// Provides clear semantic meaning and proper contrast
class FeedbackButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final bool isSelected;
  final String label;
  final Color? selectedColor;
  final Color? unselectedColor;

  const FeedbackButton({
    super.key,
    required this.icon,
    required this.onPressed,
    required this.isSelected,
    required this.label,
    this.selectedColor,
    this.unselectedColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveSelectedColor = selectedColor ?? theme.colorScheme.primary;
    final effectiveUnselectedColor = unselectedColor ?? Colors.white70;

    return AccessibleIconButton(
      icon: icon,
      onPressed: onPressed,
      color: isSelected ? effectiveSelectedColor : effectiveUnselectedColor,
      tooltip: label,
      semanticLabel: isSelected ? '$label (selected)' : label,
    );
  }
}