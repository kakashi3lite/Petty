import 'package:flutter/material.dart';
import 'design_system.dart';

// Loading State Indicator
class LoadingStateIndicator extends StatelessWidget {
  const LoadingStateIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return const CircularProgressIndicator(
      valueColor: AlwaysStoppedAnimation<Color>(kPrimaryColor),
    );
  }
}

// Primary Action Button
class PrimaryActionButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final bool isLoading;

  const PrimaryActionButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: kPrimaryColor,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(
          horizontal: kSpacingUnit * 3,
          vertical: kSpacingUnit * 2,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(kBorderRadius),
        ),
      ),
      child: isLoading
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : Text(text, style: AppTypography.body.copyWith(color: Colors.white)),
    );
  }
}

// Pet Status Card
class PetStatusCard extends StatelessWidget {
  final String petName;
  final String avatarUrl;
  final String statusText;

  const PetStatusCard({
    super.key,
    required this.petName,
    required this.avatarUrl,
    required this.statusText,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(kSpacingUnit * 2),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(kBorderRadius),
        boxShadow: [kSoftShadow],
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 30,
            backgroundImage: NetworkImage(avatarUrl),
            backgroundColor: Colors.grey[200],
          ),
          const SizedBox(width: kSpacingUnit * 2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  petName,
                  style: AppTypography.h3,
                ),
                const SizedBox(height: kSpacingUnit / 2),
                Text(
                  statusText,
                  style: AppTypography.body.copyWith(color: Colors.grey[600]),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// Activity Timeline Tile
class ActivityTimelineTile extends StatelessWidget {
  final IconData icon;
  final String activityName;
  final String time;
  final String summary;
  final bool isFirst;
  final bool isLast;

  const ActivityTimelineTile({
    super.key,
    required this.icon,
    required this.activityName,
    required this.time,
    required this.summary,
    this.isFirst = false,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: kSpacingUnit),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              if (!isFirst)
                Container(
                  width: 2,
                  height: kSpacingUnit,
                  color: Colors.grey[300],
                ),
              Container(
                padding: const EdgeInsets.all(kSpacingUnit),
                decoration: BoxDecoration(
                  color: kPrimaryColor,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  icon,
                  color: Colors.white,
                  size: 16,
                ),
              ),
              if (!isLast)
                Container(
                  width: 2,
                  height: 40,
                  color: Colors.grey[300],
                ),
            ],
          ),
          const SizedBox(width: kSpacingUnit * 2),
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(kSpacingUnit * 2),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(kBorderRadius),
                boxShadow: [kSoftShadow],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        activityName,
                        style: AppTypography.h3.copyWith(fontSize: 16),
                      ),
                      Text(
                        time,
                        style: AppTypography.caption,
                      ),
                    ],
                  ),
                  const SizedBox(height: kSpacingUnit / 2),
                  Text(
                    summary,
                    style: AppTypography.body.copyWith(fontSize: 14),
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

// Health Metric Chart (Simple placeholder implementation)
class HealthMetricChart extends StatelessWidget {
  const HealthMetricChart({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 120,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            kPrimaryColor.withOpacity(0.2),
            kSecondaryColor.withOpacity(0.2),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(kBorderRadius / 2),
      ),
      child: CustomPaint(
        painter: _ChartPainter(),
      ),
    );
  }
}

// Simple chart painter for the health metrics
class _ChartPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = kPrimaryColor
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final path = Path();
    final points = [0.2, 0.5, 0.3, 0.8, 0.6, 0.4, 0.9, 0.7];
    
    for (int i = 0; i < points.length; i++) {
      final x = (i / (points.length - 1)) * size.width;
      final y = (1 - points[i]) * size.height;
      
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    
    canvas.drawPath(path, paint);
    
    // Draw dots at data points
    final dotPaint = Paint()
      ..color = kPrimaryColor
      ..style = PaintingStyle.fill;
      
    for (int i = 0; i < points.length; i++) {
      final x = (i / (points.length - 1)) * size.width;
      final y = (1 - points[i]) * size.height;
      canvas.drawCircle(Offset(x, y), 4, dotPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}