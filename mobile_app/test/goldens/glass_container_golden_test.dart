import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';
import 'package:petty/src/widgets/glass_container.dart';

void main() {
  group('GlassContainer Golden Tests', () {
    testGoldens('GlassContainer default appearance', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: const MaterialApp(
            home: Scaffold(
              backgroundColor: Color(0xFF2193b0),
              body: Center(
                child: GlassContainer(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Text(
                      'Sample Content',
                      style: TextStyle(color: Colors.white, fontSize: 16),
                    ),
                  ),
                ),
              ),
            ),
          ),
          name: 'default',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'glass_container_default');
    });

    testGoldens('GlassContainer with custom opacity and border', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: const MaterialApp(
            home: Scaffold(
              backgroundColor: Color(0xFF2193b0),
              body: Center(
                child: GlassContainer(
                  opacity: 0.25,
                  borderAlpha: 0.5,
                  radius: 15,
                  child: Padding(
                    padding: EdgeInsets.all(20.0),
                    child: Text(
                      'Custom Glass',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
          name: 'custom_opacity_border',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'glass_container_custom');
    });

    testGoldens('GlassContainer with different radius values', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: const MaterialApp(
            home: Scaffold(
              backgroundColor: Color(0xFF6dd5ed),
              body: Column(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  GlassContainer(
                    radius: 5,
                    child: Padding(
                      padding: EdgeInsets.all(12.0),
                      child: Text(
                        'Small Radius (5)',
                        style: TextStyle(color: Colors.white),
                      ),
                    ),
                  ),
                  GlassContainer(
                    radius: 20,
                    child: Padding(
                      padding: EdgeInsets.all(12.0),
                      child: Text(
                        'Medium Radius (20)',
                        style: TextStyle(color: Colors.white),
                      ),
                    ),
                  ),
                  GlassContainer(
                    radius: 40,
                    child: Padding(
                      padding: EdgeInsets.all(12.0),
                      child: Text(
                        'Large Radius (40)',
                        style: TextStyle(color: Colors.white),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          name: 'different_radius',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'glass_container_radius_variants');
    });

    testGoldens('GlassContainer light and dark theme', (tester) async {
      final builder = DeviceBuilder()
        ..overrideDevicesForAllScenarios(devices: [Device.phone])
        ..addScenario(
          widget: MaterialApp(
            theme: ThemeData.light(),
            home: const Scaffold(
              backgroundColor: Color(0xFF2193b0),
              body: Center(
                child: GlassContainer(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.pets, color: Colors.white, size: 32),
                        SizedBox(height: 8),
                        Text(
                          'Light Theme',
                          style: TextStyle(color: Colors.white, fontSize: 16),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          name: 'light_theme',
        )
        ..addScenario(
          widget: MaterialApp(
            theme: ThemeData.dark(),
            home: const Scaffold(
              backgroundColor: Color(0xFF1a1a2e),
              body: Center(
                child: GlassContainer(
                  opacity: 0.15,
                  borderAlpha: 0.3,
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.pets, color: Colors.white, size: 32),
                        SizedBox(height: 8),
                        Text(
                          'Dark Theme',
                          style: TextStyle(color: Colors.white, fontSize: 16),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          name: 'dark_theme',
        );

      await tester.pumpDeviceBuilder(builder);
      await screenMatchesGolden(tester, 'glass_container_themes');
    });
  });
}