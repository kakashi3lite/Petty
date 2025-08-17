"""
Production-grade behavioral interpreter with security and observability.
Implements OWASP LLM Top 10 mitigations for AI systems.
"""

from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, pstdev
from math import hypot
from datetime import datetime, timezone
import uuid
import logging
from dataclasses import dataclass
from enum import Enum

# Import our security and observability modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import interpreter configuration
from .config import config

try:
    from common.security.input_validators import CollarDataModel, BehaviorEventModel
    from common.security.output_schemas import BehaviorAnalysisOutput, TimelineEventOutput
    from common.security.rate_limiter import rate_limit_decorator, CircuitBreaker
    from common.observability.logger import get_logger, log_with_context
except ImportError:
    # Fallback for development without dependencies
    logging.warning("Security and observability modules not available - using fallbacks")
    
    def rate_limit_decorator(endpoint: str, tokens: int = 1, key_func=None):
        def decorator(func):
            return func
        return decorator
    
    def log_with_context(func):
        return func
    
    class CircuitBreaker:
        def __init__(self, failure_threshold=5, timeout=60):
            self.failure_threshold = failure_threshold
            self.timeout = timeout
            
        def call(self, func, *args, **kwargs):
            return func(*args, **kwargs)

logger = logging.getLogger(__name__)

class BehaviorType(Enum):
    """Enumeration of allowed behavior types"""
    DEEP_SLEEP = "Deep Sleep"
    ANXIOUS_PACING = "Anxious Pacing"
    PLAYING_FETCH = "Playing Fetch"
    EATING = "Eating"
    DRINKING = "Drinking"
    WALKING = "Walking"
    RUNNING = "Running"
    RESTING = "Resting"
    ALERT = "Alert"
    UNKNOWN = "Unknown"

@dataclass
class BehaviorRule:
    """Immutable behavior detection rule"""
    name: str
    min_data_points: int
    confidence_threshold: float
    activity_levels: List[int]
    heart_rate_range: Tuple[int, int]
    description: str

class BehavioralInterpreter:
    """
    Production-grade behavioral interpreter with security controls.
    
    Implements:
    - Input validation (OWASP LLM01: Prompt Injection prevention)
    - Output sanitization (OWASP LLM02: Insecure Output Handling)
    - Rate limiting (OWASP LLM04: Model DoS protection)
    - Circuit breaker for resilience
    - Structured logging and observability
    """
    
    def __init__(self):
        self.logger = logger
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60
        )
        
        # Load interpreter configuration
        self.config = config
        
        # Log configuration for auditability
        try:
            self.logger.info(
                "Behavioral interpreter initialized",
                thresholds=self.config.to_dict()
            )
        except TypeError:
            # Fallback for basic logger without structured logging support
            self.logger.info(f"Behavioral interpreter initialized with thresholds: {self.config.to_dict()}")
        
        # Versioned behavior rules for auditability
        self.behavior_rules = self._load_behavior_rules()
        self.rule_version = "1.0.0"
    
    def _load_behavior_rules(self) -> Dict[str, BehaviorRule]:
        """Load immutable behavior detection rules"""
        return {
            "deep_sleep": BehaviorRule(
                name=BehaviorType.DEEP_SLEEP.value,
                min_data_points=4,
                confidence_threshold=0.9,
                activity_levels=[0],
                heart_rate_range=(40, 65),
                description="Extended period of minimal activity with stable, low heart rate"
            ),
            "anxious_pacing": BehaviorRule(
                name=BehaviorType.ANXIOUS_PACING.value,
                min_data_points=6,
                confidence_threshold=0.75,
                activity_levels=[1],
                heart_rate_range=(70, 110),
                description="Repetitive movement in small area with elevated heart rate"
            ),
            "playing_fetch": BehaviorRule(
                name=BehaviorType.PLAYING_FETCH.value,
                min_data_points=4,
                confidence_threshold=0.8,
                activity_levels=[0, 2],
                heart_rate_range=(80, 160),
                description="High activity followed by rest with significant location changes"
            )
        }
    
    @rate_limit_decorator("ai_inference", tokens=2)
    @log_with_context
    def analyze_timeline(self, collar_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze collar data timeline to detect behaviors.
        
        Args:
            collar_data: List of validated collar sensor readings
            
        Returns:
            List of detected behavioral events with metadata
        Returns:
            List of detected behavior events with confidence scores
            
        Raises:
            ValueError: If input data is invalid
            RateLimitExceeded: If rate limit is exceeded
        """
        try:
            return self.circuit_breaker.call(self._analyze_timeline_internal, collar_data)
        except Exception as e:
            try:
                self.logger.error(
                    "Behavior analysis failed",
                    error=str(e),
                    data_points=len(collar_data) if collar_data else 0,
                    rule_version=self.rule_version
                )
            except TypeError:
                data_points = len(collar_data) if collar_data else 0
                self.logger.error(f"Behavior analysis failed: {str(e)}, data points: {data_points}, rule version: {self.rule_version}")
            raise
    
    def _analyze_timeline_internal(self, collar_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Internal analysis with security controls"""
        events = []
        
        if not collar_data:
            self.logger.warning("Empty collar data provided for analysis")
            return events
        
        # Validate and sanitize input data
        validated_data = self._validate_input_data(collar_data)
        
        try:
            self.logger.info(
                "Starting behavior analysis",
                data_points=len(validated_data),
                rule_version=self.rule_version
            )
        except TypeError:
            # Fallback for basic logger
            self.logger.info(f"Starting behavior analysis: {len(validated_data)} data points, rule version {self.rule_version}")
        
        # Apply behavior detection rules
        for rule_name, rule in self.behavior_rules.items():
            try:
                detected_events = self._apply_behavior_rule(validated_data, rule)
                events.extend(detected_events)
                
                try:
                    self.logger.debug(
                        "Applied behavior rule",
                        rule_name=rule_name,
                        events_detected=len(detected_events)
                    )
                except TypeError:
                    self.logger.debug(f"Applied behavior rule {rule_name}: {len(detected_events)} events detected")
            except Exception as e:
                try:
                    self.logger.warning(
                        "Behavior rule failed",
                        rule_name=rule_name,
                        error=str(e)
                    )
                except TypeError:
                    self.logger.warning(f"Behavior rule {rule_name} failed: {str(e)}")
                # Continue with other rules on failure
                continue
        
        # Validate and sanitize output
        sanitized_events = self._validate_output_events(events)
        
        try:
            self.logger.info(
                "Behavior analysis completed",
                total_events=len(sanitized_events),
                behaviors_detected=[e.get("behavior") for e in sanitized_events]
            )
        except TypeError:
            behaviors = [e.get("behavior") for e in sanitized_events]
            self.logger.info(f"Behavior analysis completed: {len(sanitized_events)} events, behaviors: {behaviors}")
        
        return sanitized_events
    
    def _validate_input_data(self, collar_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and sanitize input collar data"""
        validated_data = []
        
        for i, data_point in enumerate(collar_data[:1000]):  # Limit to 1000 points for DoS protection
            try:
                # Basic validation - in production would use CollarDataModel
                if not isinstance(data_point, dict):
                    continue
                
                # Validate required fields
                required_fields = ["timestamp", "heart_rate", "activity_level", "location"]
                if not all(field in data_point for field in required_fields):
                    self.logger.warning(f"Missing required fields in data point {i}")
                    continue
                
                # Validate data types and ranges
                hr = data_point.get("heart_rate")
                activity = data_point.get("activity_level")
                
                if not isinstance(hr, (int, float)) or not (30 <= hr <= 300):
                    self.logger.warning(f"Invalid heart rate in data point {i}: {hr}")
                    continue
                
                if not isinstance(activity, int) or not (0 <= activity <= 2):
                    self.logger.warning(f"Invalid activity level in data point {i}: {activity}")
                    continue
                
                validated_data.append(data_point)
                
            except Exception as e:
                self.logger.warning(f"Failed to validate data point {i}: {e}")
                continue
        
        return validated_data
    
    def _validate_output_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and sanitize output events"""
        sanitized_events = []
        
        for event in events[:50]:  # Limit output size
            try:
                # Ensure required fields
                if not all(key in event for key in ["timestamp", "behavior", "confidence", "event_id"]):
                    continue
                
                # Sanitize event data
                sanitized_event = {
                    "timestamp": event["timestamp"],
                    "behavior": str(event["behavior"])[:100],  # Limit length
                    "confidence": min(max(float(event["confidence"]), 0.0), 1.0),  # Clamp confidence
                    "event_id": str(event["event_id"])[:20],  # Limit length
                }
                
                # Add optional metadata if present
                if "metadata" in event and isinstance(event["metadata"], dict):
                    sanitized_metadata = {}
                    for k, v in list(event["metadata"].items())[:5]:  # Max 5 metadata fields
                        sanitized_metadata[str(k)[:50]] = str(v)[:200]
                    sanitized_event["metadata"] = sanitized_metadata
                
                # Note: _rationale field is intentionally excluded from API response
                # It's only used for internal logging and auditing
                
                sanitized_events.append(sanitized_event)
                
            except Exception as e:
                self.logger.warning(f"Failed to sanitize event: {e}")
                continue
        
        return sanitized_events
    
    def _apply_behavior_rule(self, data: List[Dict[str, Any]], rule: BehaviorRule) -> List[Dict[str, Any]]:
        """Apply a specific behavior detection rule"""
        events = []
        
        if rule.name == BehaviorType.DEEP_SLEEP.value:
            events.extend(self._detect_deep_sleep(data, rule))
        elif rule.name == BehaviorType.ANXIOUS_PACING.value:
            events.extend(self._detect_anxious_pacing(data, rule))
        elif rule.name == BehaviorType.PLAYING_FETCH.value:
            events.extend(self._detect_playing_fetch(data, rule))
        
        return events
    
    def _detect_deep_sleep(self, data: List[Dict[str, Any]], rule: BehaviorRule) -> List[Dict[str, Any]]:
        """Detect deep sleep behavior"""
        events = []
        
        # Filter for low activity periods
        low_activity = [p for p in data if p.get("activity_level") == 0]
        
        if len(low_activity) >= rule.min_data_points:
            heart_rates = [p.get("heart_rate", 0) for p in low_activity]
            
            if heart_rates:
                try:
                    hr_mean = mean(heart_rates)
                    hr_std = pstdev(heart_rates) if len(heart_rates) > 1 else 0
                    
                    # Use configurable threshold instead of magic number
                    hr_variance_threshold = self.config.get_threshold('deep_sleep', 'hr_variance')
                    
                    # Check if matches deep sleep criteria
                    if (hr_std < hr_variance_threshold and 
                        rule.heart_rate_range[0] <= hr_mean <= rule.heart_rate_range[1]):
                        
                        # Create rationale for internal logging
                        rationale = (
                            f"Low heart rate variability ({hr_std:.2f} < {hr_variance_threshold}) "
                            f"with stable HR ({hr_mean:.1f} in range {rule.heart_rate_range}) "
                            f"during {len(low_activity)} low-activity periods"
                        )
                        
                        event = {
                            "timestamp": low_activity[0].get("timestamp"),
                            "behavior": rule.name,
                            "confidence": rule.confidence_threshold,
                            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                            "metadata": {
                                "heart_rate_mean": round(hr_mean, 1),
                                "heart_rate_std": round(hr_std, 2),
                                "duration_points": len(low_activity)
                            },
                            "_rationale": rationale  # Internal field for logging only
                        }
                        
                        # Log rationale for internal audit
                        try:
                            self.logger.debug(
                                "Deep sleep detected",
                                event_id=event["event_id"],
                                rationale=rationale
                            )
                        except TypeError:
                            # Fallback for basic logger
                            self.logger.debug(f"Deep sleep detected - {event['event_id']}: {rationale}")
                        
                        events.append(event)
                except Exception as e:
                    self.logger.warning(f"Deep sleep detection failed: {e}")
        
        return events
    
    def _detect_anxious_pacing(self, data: List[Dict[str, Any]], rule: BehaviorRule) -> List[Dict[str, Any]]:
        """Detect anxious pacing behavior"""
        events = []
        
        # Filter for moderate activity
        moderate_activity = [p for p in data if p.get("activity_level") == 1]
        
        if len(moderate_activity) >= rule.min_data_points:
            try:
                # Extract coordinates safely
                coords = []
                for p in moderate_activity:
                    loc = p.get("location", {})
                    coordinates = loc.get("coordinates", [0, 0])
                    if len(coordinates) >= 2:
                        coords.append((float(coordinates[0]), float(coordinates[1])))
                
                if len(coords) >= rule.min_data_points:
                    # Calculate movement radius
                    xs, ys = zip(*coords)
                    cx, cy = mean(xs), mean(ys)
                    radius = max(hypot(x - cx, y - cy) for x, y in coords)
                    
                    # Check heart rate
                    heart_rates = [p.get("heart_rate", 0) for p in moderate_activity]
                    hr_mean = mean(heart_rates) if heart_rates else 0
                    
                    # Use configurable threshold instead of magic number
                    radius_threshold = self.config.get_threshold('anxious_pacing', 'radius')
                    
                    # Small radius + elevated HR = anxious pacing
                    if (radius < radius_threshold and
                        rule.heart_rate_range[0] <= hr_mean <= rule.heart_rate_range[1]):
                        
                        # Create rationale for internal logging
                        rationale = (
                            f"Small movement radius ({radius:.6f} < {radius_threshold}) "
                            f"with elevated HR ({hr_mean:.1f} in range {rule.heart_rate_range}) "
                            f"over {len(moderate_activity)} moderate-activity periods"
                        )
                        
                        event = {
                            "timestamp": moderate_activity[0].get("timestamp"),
                            "behavior": rule.name,
                            "confidence": rule.confidence_threshold,
                            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                            "metadata": {
                                "movement_radius": round(radius, 6),
                                "heart_rate_mean": round(hr_mean, 1),
                                "activity_points": len(moderate_activity)
                            },
                            "_rationale": rationale  # Internal field for logging only
                        }
                        
                        # Log rationale for internal audit
                        try:
                            self.logger.debug(
                                "Anxious pacing detected",
                                event_id=event["event_id"],
                                rationale=rationale
                            )
                        except TypeError:
                            # Fallback for basic logger
                            self.logger.debug(f"Anxious pacing detected - {event['event_id']}: {rationale}")
                        
                        events.append(event)
            except Exception as e:
                self.logger.warning(f"Anxious pacing detection failed: {e}")
        
        return events
    
    def _detect_playing_fetch(self, data: List[Dict[str, Any]], rule: BehaviorRule) -> List[Dict[str, Any]]:
        """Detect playing fetch behavior"""
        events = []
        
        try:
            # Sort data by timestamp
            sorted_data = sorted(data, key=lambda p: p.get("timestamp", ""))
            
            # Look for high->low activity cycles with distance
            cycles = 0
            last_high_activity = None
            
            # Use configurable threshold instead of magic number
            distance_threshold = self.config.get_threshold('playing_fetch', 'distance')
            
            for point in sorted_data:
                activity = point.get("activity_level", 0)
                
                if activity == 2:  # High activity
                    last_high_activity = point
                elif activity == 0 and last_high_activity:  # Low activity after high
                    # Calculate distance moved
                    distance = self._calculate_distance(last_high_activity, point)
                    
                    if distance > distance_threshold:
                        cycles += 1
                        last_high_activity = None
            
            # If enough cycles detected, it's likely fetch
            if cycles >= 2:
                # Create rationale for internal logging
                rationale = (
                    f"Detected {cycles} high->low activity cycles "
                    f"with movement distance > {distance_threshold} "
                    f"across {len(sorted_data)} data points"
                )
                
                event = {
                    "timestamp": sorted_data[0].get("timestamp"),
                    "behavior": rule.name,
                    "confidence": rule.confidence_threshold,
                    "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                    "metadata": {
                        "fetch_cycles": cycles,
                        "data_points": len(sorted_data)
                    },
                    "_rationale": rationale  # Internal field for logging only
                }
                
                # Log rationale for internal audit
                try:
                    self.logger.debug(
                        "Playing fetch detected",
                        event_id=event["event_id"],
                        rationale=rationale
                    )
                except TypeError:
                    # Fallback for basic logger
                    self.logger.debug(f"Playing fetch detected - {event['event_id']}: {rationale}")
                
                events.append(event)
        except Exception as e:
            self.logger.warning(f"Playing fetch detection failed: {e}")
        
        return events
    
    
    def _calculate_distance(self, point1: Dict[str, Any], point2: Dict[str, Any]) -> float:
        """Calculate distance between two GPS points"""
        try:
            loc1 = point1.get("location", {}).get("coordinates", [0, 0])
            loc2 = point2.get("location", {}).get("coordinates", [0, 0])
            
            if len(loc1) >= 2 and len(loc2) >= 2:
                x1, y1 = float(loc1[0]), float(loc1[1])
                x2, y2 = float(loc2[0]), float(loc2[1])
                return hypot(x2 - x1, y2 - y1)
        except (ValueError, TypeError):
            pass
        
        return 0.0
