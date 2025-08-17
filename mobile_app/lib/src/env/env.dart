/// Environment configuration for the Petty mobile app
/// 
/// This file centralizes environment-specific configurations
/// that can be overridden at build time using --dart-define flags.
library env;

/// API base URL for backend services
/// 
/// Can be overridden at build time with:
/// flutter build --dart-define=API_BASE_URL=https://api.petty.com
/// 
/// Default value 'http://10.0.2.2:3000' is suitable for Android emulator
/// connecting to a local development server running on the host machine.
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:3000',
);