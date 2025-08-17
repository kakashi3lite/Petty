import 'package:flutter/material.dart';
import '../../../widgets/glass_container.dart';

class HelpScreen extends StatelessWidget {
  const HelpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF2193b0), Color(0xFF6dd5ed)],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.white),
                        onPressed: () => Navigator.of(context).pop(),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Help & FAQ',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: Colors.white),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Expanded(
                    child: ListView(
                      children: const [
                        _FAQItem(
                          question: 'Data Privacy',
                          answer: 'Your pet\'s data is encrypted and stored securely. We never share personal information with third parties. All data transmission uses industry-standard encryption, and you can request data deletion at any time.',
                          icon: Icons.privacy_tip,
                        ),
                        SizedBox(height: 12),
                        _FAQItem(
                          question: 'How Polling Works',
                          answer: 'The app automatically checks for new data every 15 seconds when active. This adaptive polling ensures you get real-time updates about your pet\'s activity, heart rate, and location while preserving battery life.',
                          icon: Icons.sync,
                        ),
                        SizedBox(height: 12),
                        _FAQItem(
                          question: 'What "Today\'s Story" Means',
                          answer: 'Today\'s Story shows your pet\'s behavior timeline throughout the day. It includes activities like resting, walking, and playing, along with timestamps to help you understand your pet\'s daily patterns.',
                          icon: Icons.timeline,
                        ),
                        SizedBox(height: 12),
                        _FAQItem(
                          question: 'How 👍/👎 Trains the Model',
                          answer: 'When you tap thumbs up or down on behavior events, you\'re helping train our AI to better understand your pet. Positive feedback reinforces correct behavior detection, while negative feedback helps improve accuracy.',
                          icon: Icons.psychology,
                        ),
                        SizedBox(height: 12),
                        _FAQItem(
                          question: 'Contact Support',
                          answer: 'Need help? Email us at support@petty.com or visit our website. For urgent issues, use the emergency contact feature in your pet\'s profile. We typically respond within 24 hours.',
                          icon: Icons.support_agent,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FAQItem extends StatefulWidget {
  final String question;
  final String answer;
  final IconData icon;

  const _FAQItem({
    required this.question,
    required this.answer,
    required this.icon,
  });

  @override
  State<_FAQItem> createState() => _FAQItemState();
}

class _FAQItemState extends State<_FAQItem> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      child: Theme(
        data: Theme.of(context).copyWith(
          dividerColor: Colors.transparent,
        ),
        child: ExpansionTile(
          leading: Icon(
            widget.icon,
            color: Colors.white,
            size: 24,
          ),
          title: Text(
            widget.question,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
          trailing: Icon(
            _isExpanded ? Icons.expand_less : Icons.expand_more,
            color: Colors.white70,
          ),
          onExpansionChanged: (expanded) {
            setState(() {
              _isExpanded = expanded;
            });
          },
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Text(
                widget.answer,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.white70,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}