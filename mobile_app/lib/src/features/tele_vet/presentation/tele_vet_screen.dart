import 'package:flutter/material.dart';
import '../../../widgets/glass_components.dart';
import '../../../widgets/accessible_icon_button.dart';

class TeleVetScreen extends StatelessWidget {
  const TeleVetScreen({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const GlassAppBar(
        title: Text('Tele‑Vet'),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF614385), Color(0xFF516395)],
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
                // Emergency contact card
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.red.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.emergency,
                              color: Colors.red,
                              size: 24,
                            ),
                          ),
                          const SizedBox(width: 16),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Emergency Care',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                Text(
                                  '24/7 emergency veterinary support',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 14,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () => _showEmergencyOptions(context),
                          icon: const Icon(Icons.phone),
                          label: const Text('Emergency Consultation'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Regular consultation card
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.blue.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.video_call,
                              color: Colors.blue,
                              size: 24,
                            ),
                          ),
                          const SizedBox(width: 16),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Video Consultation',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 18,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                Text(
                                  'Schedule or start immediate consultation',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 14,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () => _showConsultationOptions(context),
                          icon: const Icon(Icons.video_call),
                          label: const Text('Start Consultation'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Quick services card
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Quick Services',
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
                            child: _ServiceTile(
                              icon: Icons.chat,
                              label: 'Chat Support',
                              onTap: () => _showChatSupport(context),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _ServiceTile(
                              icon: Icons.medication,
                              label: 'Prescriptions',
                              onTap: () => _showPrescriptions(context),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _ServiceTile(
                              icon: Icons.history,
                              label: 'Visit History',
                              onTap: () => _showHistory(context),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _ServiceTile(
                              icon: Icons.receipt,
                              label: 'Billing',
                              onTap: () => _showBilling(context),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Veterinarian info card
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Your Veterinarian',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 25,
                            backgroundColor: Colors.white.withOpacity(0.2),
                            child: const Icon(
                              Icons.person, 
                              size: 28, 
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(width: 16),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Dr. Sarah Johnson',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                Text(
                                  'Small Animal Veterinarian',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 14,
                                  ),
                                ),
                                Text(
                                  '⭐ 4.9 • 8 years experience',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          AccessibleIconButton(
                            icon: Icons.info_outline,
                            onPressed: () => _showVetInfo(context),
                            color: Colors.white70,
                            tooltip: 'Veterinarian info',
                            semanticLabel: 'View veterinarian information',
                          ),
                        ],
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

  void _showEmergencyOptions(BuildContext context) {
    GlassSheet.show(
      context: context,
      height: 300,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.emergency, color: Colors.red, size: 24),
              const SizedBox(width: 12),
              const Text(
                'Emergency Care',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            'If this is a life-threatening emergency, please contact your local emergency veterinary clinic immediately.',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.phone),
                  label: const Text('Call Emergency'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.video_call),
                  label: const Text('Video Call'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showConsultationOptions(BuildContext context) {
    GlassSheet.show(
      context: context,
      height: 250,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Start Consultation',
            style: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Choose how you\'d like to connect with your veterinarian.',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.video_call),
                  label: const Text('Video Call'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.schedule),
                  label: const Text('Schedule'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showChatSupport(BuildContext context) => _showComingSoon(context, 'Chat Support');
  void _showPrescriptions(BuildContext context) => _showComingSoon(context, 'Prescriptions');
  void _showHistory(BuildContext context) => _showComingSoon(context, 'Visit History');
  void _showBilling(BuildContext context) => _showComingSoon(context, 'Billing');
  void _showVetInfo(BuildContext context) => _showComingSoon(context, 'Veterinarian Info');

  void _showComingSoon(BuildContext context, String feature) {
    GlassSheet.show(
      context: context,
      height: 200,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            feature,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'This feature is coming soon! We\'re working hard to bring you the best veterinary care experience.',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 16,
            ),
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
}

class _ServiceTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ServiceTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.white.withOpacity(0.2),
            width: 1,
          ),
        ),
        child: Column(
          children: [
            Icon(icon, color: Colors.white, size: 28),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
