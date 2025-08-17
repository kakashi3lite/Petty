# Petty Mobile App 🐾

Flutter mobile application for the Petty AI-powered pet monitoring platform.

## Configuration

### API Base URL

The app reads the API base URL from environment variables, allowing flexible deployment configurations:

```bash
# Development (Android emulator connecting to local server)
flutter run  # Uses default: http://10.0.2.2:3000

# Production or custom API endpoint
flutter run --dart-define=API_BASE_URL=https://api.petty.com

# Build with custom API
flutter build apk --dart-define=API_BASE_URL=https://api.petty.com
```

### Certificate Pinning

For enhanced security in production environments, the app includes a certificate pinning scaffold:

```dart
// Standard API service (no pinning)
final api = APIService();

// API service with certificate pinning enabled
final secureApi = APIService.withPinning();
```

**⚠️ Security Note**: Before using certificate pinning in production, you must:

1. Generate certificate hashes for your API endpoints
2. Update the `_pinnedCertificateHashes` list in `lib/src/services/pinned_http_client.dart`
3. Implement proper certificate validation logic

See TODOs in `pinned_http_client.dart` for detailed instructions.

## Architecture

- **`lib/src/env/`** - Environment configuration
- **`lib/src/services/`** - API services and HTTP clients
- **`lib/src/features/`** - Feature-based UI components
- **`lib/src/widgets/`** - Reusable UI components
- **`lib/src/models/`** - Data models

## Development

The app is designed to work with the Petty backend services. For local development, ensure your backend is running on port 3000, and the Android emulator will connect via the default `http://10.0.2.2:3000` endpoint.