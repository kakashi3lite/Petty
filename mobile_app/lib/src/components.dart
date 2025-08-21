import 'package:flutter/material.dart';
import 'design_system.dart';

// Loading state indicator component
class LoadingStateIndicator extends StatelessWidget {
  const LoadingStateIndicator({super.key});

  @override
  Widget build(BuildContext context) {
    return const CircularProgressIndicator(
      valueColor: AlwaysStoppedAnimation<Color>(kPrimaryColor),
    );
  }
}

// Primary action button component
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
          : Text(text, style: AppTypography.body.copyWith(fontWeight: FontWeight.w600)),
    );
  }
}

// Pet status card component
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
      padding: const EdgeInsets.all(kSpacingUnit * 3),
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
            onBackgroundImageError: (_, __) {},
            child: const Icon(Icons.pets, color: Colors.white),
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
                  style: AppTypography.body.copyWith(
                    color: Colors.grey[600],
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

// Activity timeline tile component
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
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              if (!isFirst)
                Container(
                  width: 2,
                  height: kSpacingUnit * 2,
                  color: kPrimaryColor.withOpacity(0.3),
                ),
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: kPrimaryColor,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  icon,
                  color: Colors.white,
                  size: 20,
                ),
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 2,
                    color: kPrimaryColor.withOpacity(0.3),
                  ),
                ),
            ],
          ),
          const SizedBox(width: kSpacingUnit * 2),
          Expanded(
            child: Container(
              margin: const EdgeInsets.only(bottom: kSpacingUnit * 3),
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
                        style: AppTypography.caption.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: kSpacingUnit),
                  Text(
                    summary,
                    style: AppTypography.body.copyWith(
                      color: Colors.grey[700],
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

// Health metric chart component (placeholder)
class HealthMetricChart extends StatelessWidget {
  const HealthMetricChart({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(kBorderRadius / 2),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.trending_up,
              size: 32,
              color: kPrimaryColor,
            ),
            const SizedBox(height: kSpacingUnit),
            Text(
              'Chart Data',
              style: AppTypography.caption.copyWith(
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      ),
    );
  }
}