#!/usr/bin/env python3
"""
Telemetry Sample Generator for Petty Pet Monitoring System

Generates deterministic sample telemetry data for testing and development:
- Deterministic generation using seed for reproducibility
- Configurable activity patterns: resting, walk, play, mixed
- Realistic heart rate ranges based on activity
- GPS coordinate variation around starting point
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


def parse_geo_coordinates(geo_str: str) -> Tuple[float, float]:
    """Parse 'lon,lat' string into longitude and latitude floats."""
    try:
        parts = geo_str.split(',')
        if len(parts) != 2:
            raise ValueError("Geo coordinates must be in 'lon,lat' format")
        lon, lat = float(parts[0].strip()), float(parts[1].strip())
        
        # Validate coordinate bounds
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
            
        return lon, lat
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid geo coordinates '{geo_str}': {e}")


def parse_heart_rate_range(hr_range_str: str) -> Tuple[int, int]:
    """Parse heart rate range string like '60-100' into min and max values."""
    try:
        if '-' not in hr_range_str:
            # Single value, use as both min and max
            hr = int(hr_range_str)
            return hr, hr
        
        parts = hr_range_str.split('-')
        if len(parts) != 2:
            raise ValueError("Heart rate range must be in 'min-max' or 'value' format")
        
        min_hr, max_hr = int(parts[0].strip()), int(parts[1].strip())
        
        # Validate heart rate bounds (based on dog physiology)
        if not (30 <= min_hr <= 300):
            raise ValueError(f"Minimum heart rate must be between 30-300 BPM, got {min_hr}")
        if not (30 <= max_hr <= 300):
            raise ValueError(f"Maximum heart rate must be between 30-300 BPM, got {max_hr}")
        if min_hr > max_hr:
            raise ValueError(f"Minimum heart rate ({min_hr}) cannot be greater than maximum ({max_hr})")
            
        return min_hr, max_hr
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid heart rate range '{hr_range_str}': {e}")


def get_activity_pattern_config(pattern: str) -> Dict[str, Any]:
    """Get configuration for the specified activity pattern."""
    patterns = {
        'resting': {
            'activity_weights': [0.9, 0.08, 0.02],  # Mostly level 0 (resting)
            'hr_base': 60,
            'hr_variation': 10,
            'movement_radius': 0.0001  # Very small movement while resting
        },
        'walk': {
            'activity_weights': [0.2, 0.7, 0.1],  # Mostly level 1 (walking)
            'hr_base': 80,
            'hr_variation': 15,
            'movement_radius': 0.001  # Moderate movement
        },
        'play': {
            'activity_weights': [0.1, 0.3, 0.6],  # Mostly level 2 (playing)
            'hr_base': 120,
            'hr_variation': 30,
            'movement_radius': 0.002  # High movement
        },
        'mixed': {
            'activity_weights': [0.4, 0.4, 0.2],  # Balanced mix
            'hr_base': 85,
            'hr_variation': 25,
            'movement_radius': 0.0015  # Variable movement
        }
    }
    
    if pattern not in patterns:
        raise ValueError(f"Unknown activity pattern '{pattern}'. Available: {list(patterns.keys())}")
    
    return patterns[pattern]


def generate_location(base_lon: float, base_lat: float, radius: float) -> Dict[str, Any]:
    """Generate a GPS location within radius of the base coordinates."""
    # Generate random offset within circular radius
    angle = random.uniform(0, 2 * 3.14159)  # Random angle in radians
    distance = random.uniform(0, radius)  # Random distance within radius
    
    # Convert to coordinate offsets (approximate)
    lon_offset = distance * random.uniform(-1, 1)
    lat_offset = distance * random.uniform(-1, 1)
    
    return {
        "type": "Point",
        "coordinates": [base_lon + lon_offset, base_lat + lat_offset]
    }


def generate_telemetry_sample(
    collar_id: str,
    timestamp: datetime,
    pattern_config: Dict[str, Any],
    hr_range: Optional[Tuple[int, int]] = None,
    base_coords: Tuple[float, float] = (-74.0060, 40.7128)
) -> Dict[str, Any]:
    """Generate a single telemetry sample."""
    
    # Determine activity level based on pattern weights
    activity_level = random.choices([0, 1, 2], weights=pattern_config['activity_weights'])[0]
    
    # Generate heart rate
    if hr_range:
        hr_min, hr_max = hr_range
        heart_rate = random.randint(hr_min, hr_max)
    else:
        base_hr = pattern_config['hr_base']
        variation = pattern_config['hr_variation']
        heart_rate = base_hr + random.randint(-variation, variation)
        # Clamp to valid range
        heart_rate = max(30, min(300, heart_rate))
    
    # Generate location
    base_lon, base_lat = base_coords
    location = generate_location(base_lon, base_lat, pattern_config['movement_radius'])
    
    return {
        "collar_id": collar_id,
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "heart_rate": heart_rate,
        "activity_level": activity_level,
        "location": location
    }


def generate_sample_data(
    collar_id: str,
    count: int,
    seed: int,
    activity_pattern: str,
    hr_range: Optional[Tuple[int, int]] = None,
    start_geo: Tuple[float, float] = (-74.0060, 40.7128),
    interval_minutes: int = 5
) -> List[Dict[str, Any]]:
    """Generate deterministic sample telemetry data."""
    
    # Set random seed for deterministic results
    random.seed(seed)
    
    # Get pattern configuration
    pattern_config = get_activity_pattern_config(activity_pattern)
    
    # Generate samples
    samples = []
    start_time = datetime.now(timezone.utc)
    
    for i in range(count):
        # Calculate timestamp with interval
        timestamp = start_time + timedelta(minutes=i * interval_minutes)
        
        # Generate sample
        sample = generate_telemetry_sample(
            collar_id=collar_id,
            timestamp=timestamp,
            pattern_config=pattern_config,
            hr_range=hr_range,
            base_coords=start_geo
        )
        
        samples.append(sample)
    
    return samples


def validate_collar_id(collar_id: str) -> None:
    """Validate collar ID format."""
    import re
    pattern = re.compile(r'^[A-Z]{2}-\d{3,6}$')
    if not pattern.match(collar_id):
        raise ValueError(f"Invalid collar ID format '{collar_id}'. Expected format: XX-123 (2 letters, dash, 3-6 digits)")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate deterministic telemetry samples',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Activity Patterns:
  resting - Low activity, low heart rate, minimal movement
  walk    - Moderate activity, medium heart rate, steady movement
  play    - High activity, elevated heart rate, dynamic movement  
  mixed   - Balanced mix of all activity levels

Examples:
  %(prog)s --collar-id SN-123 --count 100 --seed 42 --activity-pattern walk
  %(prog)s --collar-id SN-456 --count 50 --seed 123 --activity-pattern play --hr-range 90-150
  %(prog)s --collar-id SN-789 --count 200 --seed 999 --activity-pattern mixed --start-geo "-73.935,40.730"
        """
    )
    
    parser.add_argument(
        '--collar-id', '-c',
        required=True,
        help='Collar ID for generated samples (e.g., SN-123)'
    )
    parser.add_argument(
        '--count', '-n',
        type=int,
        required=True,
        help='Number of samples to generate'
    )
    parser.add_argument(
        '--seed', '-s',
        type=int,
        required=True,
        help='Random seed for deterministic generation'
    )
    parser.add_argument(
        '--activity-pattern', '-p',
        choices=['resting', 'walk', 'play', 'mixed'],
        required=True,
        help='Activity pattern for samples'
    )
    parser.add_argument(
        '--hr-range',
        help='Heart rate range in BPM (e.g., "60-100" or "75"). If not specified, uses pattern defaults.'
    )
    parser.add_argument(
        '--start-geo',
        default='-74.0060,40.7128',
        help='Starting GPS coordinates as "lon,lat" (default: NYC coordinates)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Interval between samples in minutes (default: 5)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file (if not specified, prints to stdout)'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate collar ID format
        validate_collar_id(args.collar_id)
        
        # Parse arguments
        start_coords = parse_geo_coordinates(args.start_geo)
        hr_range = parse_heart_rate_range(args.hr_range) if args.hr_range else None
        
        # Validate count
        if args.count <= 0:
            raise ValueError("Count must be positive")
        if args.count > 10000:
            raise ValueError("Count cannot exceed 10,000 for safety")
        
        # Generate samples
        print(f"Generating {args.count} samples for collar {args.collar_id} (pattern: {args.activity_pattern}, seed: {args.seed})...", file=sys.stderr)
        
        samples = generate_sample_data(
            collar_id=args.collar_id,
            count=args.count,
            seed=args.seed,
            activity_pattern=args.activity_pattern,
            hr_range=hr_range,
            start_geo=start_coords,
            interval_minutes=args.interval
        )
        
        # Output results
        output_data = {"samples": samples, "metadata": {
            "collar_id": args.collar_id,
            "count": len(samples),
            "seed": args.seed,
            "activity_pattern": args.activity_pattern,
            "hr_range": f"{hr_range[0]}-{hr_range[1]}" if hr_range else "pattern_default",
            "start_coordinates": start_coords,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }}
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            print(f"Generated {len(samples)} samples written to {args.output}", file=sys.stderr)
        else:
            json.dump(output_data, sys.stdout, indent=2)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())