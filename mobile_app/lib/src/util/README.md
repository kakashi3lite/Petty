# Adaptive Polling Implementation

This implementation replaces the fixed 15-second polling with an adaptive system that adjusts polling frequency based on user activity and app state.

## Key Features

### 1. Adaptive Intervals
- **5 seconds**: When app is active and user recently interacted OR data changed in last minute
- **15 seconds**: Normal usage when moderately idle (2-5 minutes)  
- **20-30 seconds**: Extended idle periods (>5 minutes)
- **12+ seconds**: Minimum debounce interval always enforced

### 2. Lifecycle-Safe Design
- Proper cleanup with `ref.onDispose()` in Riverpod providers
- App lifecycle monitoring (foreground/background state)
- No pending timers after widget disposal
- Stream cancellation on navigation away

### 3. Smart Failure Handling
- Exponential backoff on API failures (5s, 10s, 20s, 40s, max 60s)
- Jitter (±10%) to prevent thundering herd problems
- Automatic recovery on success

### 4. User Interaction Tracking
- Tap and scroll gestures influence polling rate
- Recent activity density affects intervals
- Button clicks trigger faster polling

## Files Modified

1. **`dashboard_screen.dart`**: 
   - Replaced fixed StreamProvider with adaptive version
   - Added lifecycle monitoring and user interaction tracking
   - Proper cleanup with ref.onDispose

2. **`debounced_stream.dart`** (new):
   - `PollingConfig`: Configurable timing parameters
   - `AdaptivePollingController`: Logic for interval computation
   - `DebouncedAdaptiveStream`: Stream wrapper with lifecycle management

## Test Coverage

- Timer cleanup verification (no pending timers after dispose)
- Stream cancellation on widget disposal  
- Adaptive interval computation based on activity
- Failure handling and backoff logic
- User interaction response

## Usage Example

```dart
// The provider automatically creates and manages the adaptive stream
final asyncData = ref.watch(_realTimeProvider);

// User interactions are automatically tracked
GestureDetector(
  onTap: _recordUserInteraction, // Triggers faster polling
  child: ...
)
```

## Benefits

- **Battery efficient**: Longer intervals when app is idle
- **Responsive**: Fast updates when user is active
- **Robust**: Handles failures gracefully with backoff
- **Clean**: No memory leaks or pending timers
- **Configurable**: Easy to tune intervals via PollingConfig