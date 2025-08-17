import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../widgets/glass_container.dart';

class HelpScreen extends StatefulWidget {
  const HelpScreen({super.key});

  @override
  State<HelpScreen> createState() => _HelpScreenState();
}

class _HelpScreenState extends State<HelpScreen> {
  final Set<int> _expandedItems = {};

  final List<FAQItem> _faqItems = [
    FAQItem(
      question: "How does pet behavior tracking work?",
      answer: "Petty uses advanced sensors in your pet's collar to monitor activity levels, location, and heart rate. Our AI behavioral interpreter analyzes these patterns to provide insights into your pet's well-being and activities throughout the day.",
    ),
    FAQItem(
      question: "What should I do if my pet's collar stops syncing?",
      answer: "First, check that the collar is charged and within range of your home network. Try restarting the app and ensure you have a stable internet connection. If issues persist, check the collar's LED status indicators or contact support.",
    ),
    FAQItem(
      question: "How accurate are the location readings?",
      answer: "Location tracking uses GPS with typical accuracy of 3-5 meters outdoors. Indoor accuracy may vary depending on building structure and Wi-Fi connectivity. The system updates location data every 15 seconds when your pet is active.",
    ),
    FAQItem(
      question: "Can I set custom activity goals for my pet?",
      answer: "Yes! Visit the Pet Profile section to set personalized activity targets based on your pet's age, breed, and health status. The system will track progress and provide recommendations to help maintain optimal fitness levels.",
    ),
    FAQItem(
      question: "What does the heart rate monitoring show?",
      answer: "Heart rate monitoring helps detect stress, excitement, or potential health concerns. Normal ranges vary by pet size and breed. Consistently high or low readings compared to your pet's baseline may warrant a veterinary consultation.",
    ),
    FAQItem(
      question: "How do I interpret the behavior timeline?",
      answer: "The timeline shows your pet's activities throughout the day, including resting, walking, and playing phases. You can provide feedback on accuracy using the thumbs up/down buttons to help improve our AI's predictions.",
    ),
  ];

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
            child: Column(
              children: [
                // Header with back button
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.white),
                        onPressed: () => context.go('/'),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Help & FAQ',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
                // FAQ Content
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: _faqItems.length,
                    itemBuilder: (context, index) {
                      final item = _faqItems[index];
                      final isExpanded = _expandedItems.contains(index);
                      
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: GlassContainer(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              InkWell(
                                onTap: () {
                                  setState(() {
                                    if (isExpanded) {
                                      _expandedItems.remove(index);
                                    } else {
                                      _expandedItems.add(index);
                                    }
                                  });
                                },
                                child: Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        item.question,
                                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                          color: Colors.white,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                    Icon(
                                      isExpanded ? Icons.expand_less : Icons.expand_more,
                                      color: Colors.white70,
                                    ),
                                  ],
                                ),
                              ),
                              AnimatedCrossFade(
                                firstChild: const SizedBox.shrink(),
                                secondChild: Padding(
                                  padding: const EdgeInsets.only(top: 12),
                                  child: Text(
                                    item.answer,
                                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                      color: Colors.white70,
                                      height: 1.5,
                                    ),
                                  ),
                                ),
                                crossFadeState: isExpanded 
                                    ? CrossFadeState.showSecond 
                                    : CrossFadeState.showFirst,
                                duration: const Duration(milliseconds: 200),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class FAQItem {
  final String question;
  final String answer;

  FAQItem({required this.question, required this.answer});
}