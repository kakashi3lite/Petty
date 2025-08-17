import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';
import 'package:petty/src/widgets/glass_container.dart';

/// Showcase widget demonstrating various GlassContainer configurations
class GlassContainerShowcase extends StatelessWidget {
  const GlassContainerShowcase({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'GlassContainer Showcase',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 20),
                
                // Default configuration
                const Text(
                  'Default Configuration',
                  style: TextStyle(color: Colors.white70, fontSize: 16),
                ),
                const SizedBox(height: 8),
                const GlassContainer(
                  child: Text(
                    'Default glass effect (opacity: 0.12, borderAlpha: 0.2)',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                const SizedBox(height: 20),
                
                // High opacity configuration
                const Text(
                  'High Opacity',
                  style: TextStyle(color: Colors.white70, fontSize: 16),
                ),
                const SizedBox(height: 8),
                const GlassContainer(
                  opacity: 0.3,
                  borderAlpha: 0.4,
                  child: Text(
                    'More opaque glass (opacity: 0.3, borderAlpha: 0.4)',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                const SizedBox(height: 20),
                
                // Subtle configuration
                const Text(
                  'Subtle Effect',
                  style: TextStyle(color: Colors.white70, fontSize: 16),
                ),
                const SizedBox(height: 8),
                const GlassContainer(
                  opacity: 0.05,
                  borderAlpha: 0.1,
                  child: Text(
                    'Very subtle glass (opacity: 0.05, borderAlpha: 0.1)',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                const SizedBox(height: 20),
                
                // Different radius
                const Text(
                  'Different Radius',
                  style: TextStyle(color: Colors.white70, fontSize: 16),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: GlassContainer(
                        radius: 5,
                        child: const Padding(
                          padding: EdgeInsets.all(12),
                          child: Text(
                            'Small radius (5)',
                            style: TextStyle(color: Colors.white, fontSize: 12),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: GlassContainer(
                        radius: 30,
                        child: const Padding(
                          padding: EdgeInsets.all(12),
                          child: Text(
                            'Large radius (30)',
                            style: TextStyle(color: Colors.white, fontSize: 12),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

void main() {
  group('GlassContainer Showcase Golden Tests', () {
    testGoldens('GlassContainer configuration showcase', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: const MaterialApp(
            home: GlassContainerShowcase(),
          ),
          name: 'showcase',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'glass_container_showcase');
    });
  });
}