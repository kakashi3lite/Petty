# Performance & Accessibility Guidelines

## Performance Targets

### Frame Rate Requirements
- **Target**: 60fps (16.6ms frame budget)
- **P99 Threshold**: ≤33.4ms (allows for 2x budget headroom)
- **P95 Target**: ≤16.6ms (smooth 60fps)

### Memory Guidelines
- **Peak Usage**: ≤128MB on mid-range devices
- **Cache Size**: Auto-expire data >1 hour old
- **Leak Prevention**: Proper disposal of streams and subscriptions

### APK Size Limits
- **Per-ABI Limit**: ≤30MB
- **Total Limit**: ≤90MB (3 ABIs)
- **Asset Optimization**: Compress images, minimize fonts

## Accessibility Standards

### WCAG AA Compliance
- **Color Contrast**: ≥4.5:1 for normal text, ≥3:1 for large text
- **Touch Targets**: ≥48×48dp with proper spacing
- **Focus Management**: Logical tab order, visible focus indicators
- **Screen Reader**: Semantic labels, state announcements

### Implementation Checklist
- [ ] All interactive elements have semantic labels
- [ ] Touch targets meet minimum size requirements
- [ ] Color combinations pass contrast ratio tests
- [ ] Loading states announce progress to screen readers
- [ ] Error messages are descriptive and actionable
- [ ] Form inputs have proper labels and validation

### Testing Tools
```bash
# Accessibility testing
flutter test test/accessibility/

# Semantic debugging
flutter run --enable-accessibility-debug

# Contrast validation
# Use online tools like WebAIM Contrast Checker
```

## Glassmorphism Design Tokens

### Color System
```dart
// Light theme
surfaceColor: Color(0x26FFFFFF)     // 15% white
borderColor: Color(0x33FFFFFF)      // 20% white
onSurfaceColor: Color(0xFF1A1A1A)   // AA compliant dark
onSurfaceSecondary: Color(0xFF616161) // AA compliant gray

// Dark theme  
surfaceColor: Color(0x26FFFFFF)     // 15% white
borderColor: Color(0x33FFFFFF)      // 20% white
onSurfaceColor: Color(0xFFFFFFFF)   // White text
onSurfaceSecondary: Color(0xFFE0E0E0) // AA compliant light gray
```

### Blur and Radius
```dart
blurSigma: 14.0           // Backdrop filter strength
defaultRadius: 20.0       // Corner radius
borderWidth: 1.0          // Border thickness
```

### Usage Guidelines
- Use `context.glassTheme` to access design tokens
- Apply `RepaintBoundary` to glass containers for performance
- Ensure text on glass surfaces meets contrast requirements
- Test readability across different backgrounds

## Adaptive Polling Configuration

### Default Settings
```dart
baseInterval: Duration(seconds: 15)      // Base polling frequency
maxInterval: Duration(minutes: 5)        // Max backoff interval
maxRetries: 3                           // Retry attempts before backoff
jitterRange: 0.25                       // ±25% randomization
```

### ETag Implementation
```dart
// Request headers
If-None-Match: "etag-value"

// Response handling
304 Not Modified -> Skip data processing
200 OK + ETag -> Cache new ETag for next request
```

### Performance Benefits
- **Bandwidth Reduction**: 60-80% fewer bytes with ETags
- **Battery Optimization**: Exponential backoff reduces CPU usage
- **Server Load**: Conditional requests reduce backend processing
- **User Experience**: Cached data provides instant feedback

## CI/CD Performance Gates

### Required Checks
```yaml
# APK size validation
- name: Check APK size
  run: |
    APK_SIZE_MB=$(($(stat -c%s app.apk) / 1048576))
    if [ $APK_SIZE_MB -gt 30 ]; then exit 1; fi

# Performance testing
- name: Run performance tests
  run: flutter test test/performance/

# Accessibility validation
- name: Run accessibility tests  
  run: flutter test test/accessibility/
```

### Monitoring
- **Frame time tracking**: P99 metrics in CI logs
- **Memory profiling**: Heap usage during test runs
- **Network efficiency**: ETag hit rates and bandwidth usage
- **Accessibility scores**: Automated semantic validation

## Best Practices

### Code Organization
- Extract reusable widgets with accessibility built-in
- Use theme extensions for consistent design tokens
- Implement proper error boundaries and fallbacks
- Add comprehensive test coverage for critical paths

### Performance Optimization
- Wrap expensive widgets with `RepaintBoundary`
- Use `flutter pub deps` to analyze dependency graph
- Profile with `flutter run --profile` for release performance
- Monitor memory usage with DevTools

### Accessibility Testing
- Test with screen readers enabled (VoiceOver/TalkBack)
- Verify keyboard navigation on supported platforms
- Validate color combinations with contrast checkers
- Include users with disabilities in testing process