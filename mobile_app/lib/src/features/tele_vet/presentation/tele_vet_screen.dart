import 'package:flutter/material.dart';
import '../../../widgets/glass_container.dart';

class TeleVetScreen extends StatelessWidget {
  const TeleVetScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          Container(decoration: const BoxDecoration(gradient: LinearGradient(
            colors: [Color(0xFF614385), Color(0xFF516395)],
            begin: Alignment.topCenter, end: Alignment.bottomCenter))),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Tele‑Vet', style: Theme.of(context).textTheme.headlineMedium?.copyWith(color: Colors.white)),
                const SizedBox(height: 16),
                GlassContainer(child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: (){},
                    child: const Padding(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      child: Text('Connect with a Veterinarian'),
                    ),
                  ),
                )),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}
