# Performance & Accessibility Guide

## Glassmorphism Performance Optimizations

### 1. ImageFiltered vs BackdropFilter
- **Before**: `BackdropFilter` was causing overdraw and jank in scrolling lists
- **After**: `ImageFiltered` provides contained blur with better performance
- **Result**: Eliminates unnecessary GPU work and reduces frame drops

### 2. RepaintBoundary Usage
All glass components now use `RepaintBoundary` to:
- Isolate repaints to specific widget subtrees
- Prevent cascade repaints when glass effects change
- Maintain 60fps target during scrolling and animations

### 3. ClipRRect Optimization
Glass containers are properly bounded with `ClipRRect` to:
- Prevent blur effects from leaking outside intended areas
- Reduce overdraw and improve GPU efficiency
- Enable proper layer caching

## Accessibility Compliance

### Touch Target Requirements
- **Minimum Size**: 48dp × 48dp for all interactive elements
- **Implementation**: `AccessibleIconButton` enforces constraints
- **Verification**: Automated tests check touch target dimensions

### Color Contrast Standards
- **Body Text**: ≥4.5:1 contrast ratio (WCAG AA)
- **Large Text**: ≥3.1:1 contrast ratio (WCAG AA)  
- **Implementation**: Theme tokens ensure proper contrast over glass surfaces

### Semantic Labels
- All interactive elements have descriptive semantic labels
- Screen reader support with proper button/link identification
- Focus order maintained for keyboard navigation

## Polling Performance

### Adaptive Polling Strategy
- **Base Interval**: 15 seconds for real-time data
- **Error Handling**: Exponential backoff (15s → 30s → 60s → 120s max)
- **Auto-Cleanup**: Timer cancellation on widget disposal
- **Manual Refresh**: User-triggered refresh resets error state

### Memory Management
- Stream providers use `autoDispose` to prevent memory leaks
- Timers are properly cancelled when widgets are disposed
- State is reset between polling sessions

## Frame Budget Compliance

### Target Metrics
- **Frame Time**: ≤16.6ms (60fps)
- **Jank Threshold**: <5% of frames exceed budget
- **GPU Usage**: Minimize shader compilation on critical paths

### Optimization Techniques
1. **Precompiled Shaders**: Impeller engine pre-compiles blur shaders
2. **Layer Caching**: RepaintBoundary caches expensive glass layers  
3. **Selective Updates**: Granular Riverpod providers minimize rebuilds
4. **Blur Bounds**: Small, contained blur regions vs full-screen effects

## Testing Strategy

### Automated Accessibility Tests
```dart
// Touch target verification
expect(buttonSize.width, greaterThanOrEqualTo(48.0));
expect(buttonSize.height, greaterThanOrEqualTo(48.0));

// Semantic label validation  
expect(find.bySemanticsLabel('Close sheet'), findsOneWidget);
```

### Performance Profiling
1. Run app in profile mode: `flutter run --profile`
2. Enable performance overlay: `MaterialApp(showPerformanceOverlay: true)`
3. Monitor frame times in DevTools Performance view
4. Verify Impeller rendering pipeline usage

### Manual Testing Checklist
- [ ] All touch targets ≥48dp on physical devices
- [ ] Text readable over glass surfaces in both themes
- [ ] Screen reader announces all interactive elements
- [ ] No frame drops during scrolling glass lists
- [ ] Polling stops when navigating away from screens
- [ ] Glass effects render consistently across devices

## Best Practices

### Glass Component Usage
```dart
// ✅ Good: Contained glass effect
GlassCard(child: MyContent())

// ❌ Avoid: Full-screen BackdropFilter in lists
ListView.builder(
  itemBuilder: (context, index) => BackdropFilter(...)
)
```

### State Management
```dart
// ✅ Good: Granular selectors
ref.watch(dataProvider.select((data) => data.heartRate))

// ❌ Avoid: Broad rebuilds  
ref.watch(dataProvider)
```

### Theme Integration
```dart
// ✅ Good: Use theme tokens
final tokens = context.glassTokens;

// ❌ Avoid: Hardcoded values
color: Colors.white.withOpacity(0.12)
```