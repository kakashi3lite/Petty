# Adaptive Polling & Glassmorphism Enhancement

## Overview

This enhancement implements a comprehensive improvement to the Petty Flutter app, replacing inefficient `while(true)` polling with adaptive polling, implementing consistent glassmorphism design, improving accessibility, and adding performance optimizations.

## Key Features

### 1. Adaptive Polling System
- **ETag Support**: Conditional requests with `If-None-Match` headers
- **Exponential Backoff**: Progressive delays on errors (2^n * base_interval)
- **Jitter**: ±25% randomization to prevent thundering herd
- **Debounce**: Natural rate limiting with minimum intervals
- **Circuit Breaking**: Automatic failure handling and recovery

### 2. Glassmorphism Design System
- **Consistent Tokens**: Centralized theme via `GlassmorphismTheme` extension
- **Material 3 Integration**: Dynamic color schemes with system theme support  
- **Accessibility-First**: AA-compliant contrast ratios (≥4.5:1)
- **Responsive**: Light/dark theme variants with proper color interpolation

### 3. Accessibility Improvements
- **Touch Targets**: 48×48dp minimum size for all interactive elements
- **Semantic Labels**: Comprehensive screen reader support
- **Contrast Compliance**: WCAG AA standards for all text/background combinations
- **Focus Management**: Proper navigation flow and state announcements

### 4. Performance Optimizations
- **RepaintBoundary**: Isolated rebuilds for glass containers and metrics
- **Riverpod Select**: Granular state subscriptions to minimize rebuilds
- **Offline Caching**: Persistent storage with automatic expiration
- **Memory Management**: Proper disposal and cleanup of polling streams

## Architecture

### Service Layer
```dart
- AdaptivePollingService: Smart HTTP polling with backoff
- OfflineCacheService: Local data persistence with TTL
- TelemetryService: Privacy-first analytics with user consent
- RemoteConfigService: Feature flags and configuration
```

### UI Layer  
```dart
- GlassmorphismTheme: Design system extension
- AccessibleIconButton: AA-compliant touch targets
- GlassContainer: Optimized backdrop filter with theming
- Enhanced Dashboard: Responsive, accessible, performant
```

### Testing
```dart
- Performance Tests: p99 frame time ≤33.4ms validation
- Accessibility Tests: Touch targets, semantic labels, contrast
- Integration Tests: Adaptive polling, offline scenarios
```

## Performance Metrics

### CI Gates
- **APK Size**: ≤30MB per ABI
- **Frame Performance**: p99 ≤33.4ms (60fps target)
- **Test Coverage**: Comprehensive unit/widget/accessibility tests
- **Static Analysis**: Flutter analyze with fatal-infos

### Runtime Optimizations
- **Polling Efficiency**: ETag-based conditional requests reduce bandwidth
- **Memory Usage**: Automatic cache cleanup and stream disposal
- **Render Performance**: RepaintBoundary isolation prevents cascade rebuilds
- **Battery Impact**: Exponential backoff reduces unnecessary API calls

## Accessibility Features

### WCAG AA Compliance
- **Color Contrast**: ≥4.5:1 ratio for normal text, ≥3:1 for large text
- **Touch Targets**: 48×48dp minimum with proper visual feedback
- **Semantic Structure**: Headings, labels, and role assignments
- **Screen Reader**: VoiceOver/TalkBack compatible announcements

### Responsive Design
- **Theme Adaptation**: Respects system dark/light mode preference
- **Dynamic Type**: Supports user font size preferences
- **High Contrast**: Enhanced visibility options support

## Security & Privacy

### Telemetry
- **Opt-in Only**: Explicit user consent required
- **Data Minimization**: Only essential metrics collected
- **Local Control**: User can revoke consent at any time
- **Sentry Integration**: Crash reporting and performance monitoring

### Data Protection
- **Offline-First**: Cached data encrypted at rest
- **Network Security**: TLS enforcement for all API calls
- **Token Management**: Secure storage of authentication credentials

## Migration Guide

### Breaking Changes
- `StreamProvider` polling replaced with `AdaptivePollingService`
- `Colors.white70` replaced with theme-aware colors
- `IconButton` upgraded to `AccessibleIconButton` for compliance

### Backward Compatibility
- Existing API contracts preserved
- Graceful degradation for network issues
- Cache fallbacks for offline scenarios

## Configuration

### Environment Variables
```dart
// Sentry DSN for telemetry
SENTRY_DSN=your_sentry_dsn_here

// Remote config endpoint
REMOTE_CONFIG_URL=your_config_endpoint
```

### Feature Flags
```dart
enable_adaptive_polling: true
polling_base_interval_seconds: 15
polling_max_interval_seconds: 300
cache_max_age_minutes: 60
enable_glassmorphism: true
performance_monitoring_enabled: true
```

## Development Workflow

### Testing
```bash
# Run all tests
flutter test

# Performance tests
flutter test test/performance/

# Accessibility tests  
flutter test test/accessibility/

# Build and check APK size
flutter build apk --profile
```

### CI/CD Pipeline
1. **Security Scan**: Bandit, Safety, Semgrep
2. **Code Quality**: Flutter analyze, format check
3. **Testing**: Unit, widget, integration tests
4. **Performance**: APK size, frame rate validation
5. **Accessibility**: Semantic structure verification
6. **Deployment**: Automated builds and signing

## Future Enhancements

### Planned Features
- **WebSocket Fallback**: Real-time updates when available
- **Predictive Caching**: ML-based prefetching
- **Advanced Analytics**: User behavior insights (opt-in)
- **A/B Testing**: Feature flag-based experimentation

### Performance Targets
- **p95 Frame Time**: ≤16.6ms (smooth 60fps)
- **Cold Start**: ≤2 seconds to first paint
- **Memory Usage**: ≤128MB peak on mid-range devices
- **Battery Impact**: ≤1% per hour background operation

## Support

### Debugging
- **Debug Overlays**: Performance metrics in debug builds
- **Logging**: Structured logging with severity levels
- **Telemetry Dashboard**: Real-time app health monitoring
- **Cache Inspector**: Local storage debugging tools

### Known Issues
- None currently reported

### Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and code standards.