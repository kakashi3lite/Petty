import 'package:flutter/material.dart';

// Color System
const Color kBackgroundColor = Color(0xFFF5F5F5);
const Color kPrimaryColor = Color(0xFF6750A4);
const Color kSecondaryColor = Color(0xFF6dd5ed);

// Spacing & Dimensions
const double kSpacingUnit = 8.0;
const double kBorderRadius = 12.0;

// Shadows
const BoxShadow kSoftShadow = BoxShadow(
  color: Color(0x1A000000),
  blurRadius: 8.0,
  offset: Offset(0, 2),
);

// Typography System
class AppTypography {
  static const TextStyle h1 = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    letterSpacing: -0.5,
  );
  
  static const TextStyle h2 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.25,
  );
  
  static const TextStyle h3 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
  );
  
  static const TextStyle body = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.normal,
    height: 1.5,
  );
  
  static const TextStyle caption = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.normal,
    color: Colors.grey,
  );
}