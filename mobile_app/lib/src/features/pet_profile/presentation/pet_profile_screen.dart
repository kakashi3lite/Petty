import 'package:flutter/material.dart';
import '../../..//widgets/glass_container.dart';

class PetProfileScreen extends StatelessWidget {
  const PetProfileScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          Container(decoration: const BoxDecoration(gradient: LinearGradient(
            colors: [Color(0xFF56ab2f), Color(0xFFA8E063)],
            begin: Alignment.topCenter, end: Alignment.bottomCenter))),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Pet Profile & Care Plan', style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: Colors.white)),
                const SizedBox(height: 16),
                GlassContainer(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
                  Text('Name: Buddy', style: TextStyle(color: Colors.white)),
                  SizedBox(height: 8), Text('Species: Dog', style: TextStyle(color: Colors.white)),
                  SizedBox(height: 8), Text('Breed: Labrador', style: TextStyle(color: Colors.white)),
                  SizedBox(height: 8), Text('Age: 6', style: TextStyle(color: Colors.white)),
                ])),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}
