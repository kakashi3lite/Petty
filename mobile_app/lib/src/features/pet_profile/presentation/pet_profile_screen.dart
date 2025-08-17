import 'package:flutter/material.dart';
import '../../../widgets/glass_components.dart';
import '../../../widgets/accessible_icon_button.dart';

class PetProfileScreen extends StatelessWidget {
  const PetProfileScreen({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const GlassAppBar(
        title: Text('Pet Profile & Care Plan'),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF56ab2f), Color(0xFFA8E063)],
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
                // Pet basic info card
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 30,
                            backgroundColor: Colors.white.withOpacity(0.2),
                            child: const Icon(
                              Icons.pets, 
                              size: 32, 
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(width: 16),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Buddy',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 24,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                Text(
                                  'Labrador • 6 years old',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 16,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          AccessibleIconButton(
                            icon: Icons.edit,
                            onPressed: () => _showEditDialog(context),
                            color: Colors.white,
                            tooltip: 'Edit profile',
                            semanticLabel: 'Edit pet profile',
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Health metrics card
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Health Metrics',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: _HealthMetric(
                              icon: Icons.monitor_weight,
                              label: 'Weight',
                              value: '32 kg',
                              trend: 'stable',
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: _HealthMetric(
                              icon: Icons.straighten,
                              label: 'Height',
                              value: '58 cm',
                              trend: 'stable',
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Care plan card
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Care Plan',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          AccessibleIconButton(
                            icon: Icons.calendar_today,
                            onPressed: () => _showSchedule(context),
                            color: Colors.white70,
                            tooltip: 'View schedule',
                            semanticLabel: 'View care schedule',
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      const _CareItem(
                        icon: Icons.restaurant,
                        title: 'Feeding',
                        description: '2 cups, twice daily',
                        isCompleted: true,
                      ),
                      const SizedBox(height: 12),
                      const _CareItem(
                        icon: Icons.directions_walk,
                        title: 'Exercise',
                        description: '45 minutes daily walk',
                        isCompleted: false,
                      ),
                      const SizedBox(height: 12),
                      const _CareItem(
                        icon: Icons.medical_services,
                        title: 'Medication',
                        description: 'Arthritis medication - Evening',
                        isCompleted: false,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showEditDialog(BuildContext context) {
    GlassSheet.show(
      context: context,
      height: 400,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Edit Pet Profile',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Update your pet\'s information to ensure the best care recommendations.',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 24),
          Center(
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Coming Soon'),
            ),
          ),
        ],
      ),
    );
  }

  void _showSchedule(BuildContext context) {
    GlassSheet.show(
      context: context,
      height: 300,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Care Schedule',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'View and manage your pet\'s daily care routine.',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 24),
          Center(
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('View Full Schedule'),
            ),
          ),
        ],
      ),
    );
  }
}

class _HealthMetric extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String trend;

  const _HealthMetric({
    required this.icon,
    required this.label,
    required this.value,
    required this.trend,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: Colors.white, size: 24),
        const SizedBox(height: 8),
        Text(
          label,
          style: const TextStyle(color: Colors.white70, fontSize: 14),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}

class _CareItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;
  final bool isCompleted;

  const _CareItem({
    required this.icon,
    required this.title,
    required this.description,
    required this.isCompleted,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          color: isCompleted ? Colors.greenAccent : Colors.white70,
          size: 24,
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  color: isCompleted ? Colors.greenAccent : Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                description,
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
        Icon(
          isCompleted ? Icons.check_circle : Icons.radio_button_unchecked,
          color: isCompleted ? Colors.greenAccent : Colors.white70,
          size: 20,
        ),
      ],
    );
  }
}
