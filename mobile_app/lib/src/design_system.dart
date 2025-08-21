import 'package:flutter/material.dart';

// Color constants
const Color kBackgroundColor = Color(0xFFF5F5F5);
const Color kPrimaryColor = Color(0xFF6dd5ed);
const Color kSecondaryColor = Color(0xFF2193b0);

// Spacing constants
const double kSpacingUnit = 8.0;

// Border constants
const double kBorderRadius = 12.0;

// Shadow constants
const BoxShadow kSoftShadow = BoxShadow(
  color: Color(0x1A000000),
  offset: Offset(0, 2),
  blurRadius: 8,
  spreadRadius: 0,
);

// Typography system
class AppTypography {
  static const TextStyle h1 = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    height: 1.2,
  );
  
  static const TextStyle h2 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    height: 1.3,
  );
  
  static const TextStyle h3 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
    height: 1.3,
  );
  
  static const TextStyle body = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.normal,
    height: 1.4,
  );
  
  static const TextStyle caption = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.normal,
    height: 1.4,
  );
  
  static const TextStyle label = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    height: 1.4,
  );
}