import 'package:flutter/material.dart';

/// Accessibility-compliant IconButton that enforces 48x48dp minimum touch target
class AccessibleIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final Color? color;
  final String? semanticLabel;
  final double size;
  final EdgeInsets padding;
  final bool enabled;
  
  const AccessibleIconButton({
    super.key,
    required this.icon,
    this.onPressed,
    this.color,
    this.semanticLabel,
    this.size = 24.0,
    this.padding = const EdgeInsets.all(12.0), // Ensures 48x48dp minimum
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveColor = color ?? theme.iconTheme.color;
    
    return Semantics(
      label: semanticLabel,
      button: true,
      enabled: enabled,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(24), // Circular touch area
        child: InkWell(
          borderRadius: BorderRadius.circular(24),
          onTap: enabled ? onPressed : null,
          child: Container(
            padding: padding,
            constraints: const BoxConstraints(
              minWidth: 48.0, // Minimum touch target width
              minHeight: 48.0, // Minimum touch target height
            ),
            child: Icon(
              icon,
              size: size,
              color: enabled ? effectiveColor : effectiveColor?.withOpacity(0.38),
            ),
          ),
        ),
      ),
    );
  }
}

/// Feedback button with accessible touch targets and semantic labels
class FeedbackButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final bool isSelected;
  final String feedbackType;
  final Color? selectedColor;
  final Color? unselectedColor;
  
  const FeedbackButton({
    super.key,
    required this.icon,
    this.onPressed,
    this.isSelected = false,
    required this.feedbackType,
    this.selectedColor,
    this.unselectedColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final glassTheme = theme.extension<dynamic>(); // Use dynamic to avoid import issues
    
    Color effectiveColor;
    if (isSelected) {
      effectiveColor = selectedColor ?? 
        (feedbackType == 'positive' ? Colors.greenAccent : Colors.redAccent);
    } else {
      effectiveColor = unselectedColor ?? Colors.white.withOpacity(0.87); // AA compliant
    }
    
    final semanticLabel = isSelected 
        ? '$feedbackType feedback selected'
        : 'Give $feedbackType feedback';
    
    return AccessibleIconButton(
      icon: icon,
      onPressed: onPressed,
      color: effectiveColor,
      semanticLabel: semanticLabel,
    );
  }
}