import 'package:flutter/material.dart';
import '../../../widgets/glass_components.dart';
import '../../../widgets/accessible_icon_button.dart';
import '../../../theme/app_theme.dart';

/// Component gallery to showcase glassmorphism design system
class ComponentGalleryScreen extends StatefulWidget {
  const ComponentGalleryScreen({super.key});

  @override
  State<ComponentGalleryScreen> createState() => _ComponentGalleryScreenState();
}

class _ComponentGalleryScreenState extends State<ComponentGalleryScreen> {
  int _selectedNavIndex = 0;
  bool _isDarkMode = false;

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: _isDarkMode ? AppTheme.dark() : AppTheme.light(),
      child: Scaffold(
        extendBodyBehindAppBar: true,
        appBar: GlassAppBar(
          title: const Text('Glass Components'),
          actions: [
            AccessibleIconButton(
              icon: _isDarkMode ? Icons.light_mode : Icons.dark_mode,
              onPressed: () => setState(() => _isDarkMode = !_isDarkMode),
              tooltip: 'Toggle theme',
              semanticLabel: _isDarkMode ? 'Switch to light mode' : 'Switch to dark mode',
            ),
          ],
        ),
        body: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: _isDarkMode 
                  ? [const Color(0xFF1A1A2E), const Color(0xFF16213E)]
                  : [const Color(0xFF2193b0), const Color(0xFF6dd5ed)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
          child: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 80), // Account for glass app bar
                  
                  _SectionTitle('Glass Cards'),
                  const SizedBox(height: 16),
                  
                  // Glass Card Examples
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.pets, color: Colors.white, size: 24),
                            const SizedBox(width: 12),
                            const Expanded(
                              child: Text(
                                'Pet Health Score',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          '92/100 - Excellent',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Based on activity, diet, and health metrics',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  GlassCard(
                    onTap: () => _showGlassSheet(),
                    child: Row(
                      children: [
                        Icon(Icons.touch_app, color: Colors.white, size: 24),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Text(
                            'Tap to open Glass Sheet',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                            ),
                          ),
                        ),
                        Icon(Icons.arrow_forward_ios, color: Colors.white70, size: 16),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 32),
                  
                  _SectionTitle('Accessible Buttons'),
                  const SizedBox(height: 16),
                  
                  // Button Examples
                  Wrap(
                    spacing: 16,
                    runSpacing: 16,
                    children: [
                      AccessibleIconButton(
                        icon: Icons.favorite,
                        onPressed: () => _showSnackbar('Favorite pressed'),
                        color: Colors.red,
                        tooltip: 'Add to favorites',
                        semanticLabel: 'Add to favorites',
                      ),
                      AccessibleIconButton(
                        icon: Icons.share,
                        onPressed: () => _showSnackbar('Share pressed'),
                        color: Colors.blue,
                        tooltip: 'Share',
                        semanticLabel: 'Share content',
                      ),
                      AccessibleIconButton(
                        icon: Icons.bookmark,
                        onPressed: () => _showSnackbar('Bookmark pressed'),
                        color: Colors.orange,
                        tooltip: 'Bookmark',
                        semanticLabel: 'Bookmark item',
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 32),
                  
                  _SectionTitle('Feedback Buttons'),
                  const SizedBox(height: 16),
                  
                  GlassCard(
                    child: Row(
                      children: [
                        const Expanded(
                          child: Text(
                            'Did this help your pet?',
                            style: TextStyle(color: Colors.white, fontSize: 16),
                          ),
                        ),
                        FeedbackButton(
                          icon: Icons.thumb_up,
                          isSelected: false,
                          label: 'Helpful',
                          onPressed: () => _showSnackbar('Marked as helpful'),
                        ),
                        FeedbackButton(
                          icon: Icons.thumb_down,
                          isSelected: false,
                          label: 'Not helpful',
                          onPressed: () => _showSnackbar('Marked as not helpful'),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 120), // Space for bottom nav
                ],
              ),
            ),
          ),
        ),
        bottomNavigationBar: GlassNavBar(
          currentIndex: _selectedNavIndex,
          onTap: (index) => setState(() => _selectedNavIndex = index),
          items: const [
            GlassNavItem(icon: Icons.dashboard, label: 'Dashboard'),
            GlassNavItem(icon: Icons.pets, label: 'Pets'),
            GlassNavItem(icon: Icons.medical_services, label: 'Health'),
            GlassNavItem(icon: Icons.settings, label: 'Settings'),
          ],
        ),
      ),
    );
  }

  void _showGlassSheet() {
    GlassSheet.show(
      context: context,
      height: 300,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Glass Sheet Demo',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              AccessibleIconButton(
                icon: Icons.close,
                onPressed: () => Navigator.of(context).pop(),
                color: Colors.white,
                tooltip: 'Close',
                semanticLabel: 'Close sheet',
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'This is a glassmorphism modal sheet with proper blur effects and accessibility support.',
            style: TextStyle(color: Colors.white70, fontSize: 16),
          ),
          const SizedBox(height: 24),
          Center(
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Got it'),
            ),
          ),
        ],
      ),
    );
  }

  void _showSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        backgroundColor: Colors.black87,
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  
  const _SectionTitle(this.title);

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 22,
        fontWeight: FontWeight.bold,
      ),
    );
  }
}