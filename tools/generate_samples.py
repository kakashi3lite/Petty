#!/usr/bin/env python3
"""
Telemetry Sample Generator for local testing

Generates synthetic telemetry data samples that match the DATA_PROTOCOL.md format.
Useful for testing the behavioral interpreter and other system components.
"""
import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List


def parse_geo_coordinates(geo_str: str) -> tuple[float, float]:
    """Parse 'lon,lat' string into longitude and latitude floats."""
    try:
        parts = geo_str.split(',')
        if len(parts) != 2:
            raise ValueError("Invalid format")
        lon, lat = float(parts[0]), float(parts[1])
        return lon, lat
    except (ValueError, IndexError):
        raise ValueError("Geographic coordinates must be in 'lon,lat' format (e.g., '-74.0060,40.7128')")


def parse_hr_range(hr_range_str: str) -> tuple[int, int]:
    """Parse heart rate range string like '60-120' into min and max values."""
    try:
        parts = hr_range_str.split('-')
        if len(parts) != 2:
            raise ValueError("Invalid format")
        min_hr, max_hr = int(parts[0]), int(parts[1])
        if min_hr >= max_hr or min_hr < 30 or max_hr > 200:
            raise ValueError("Invalid range")
        return min_hr, max_hr
    except (ValueError, IndexError):
        raise ValueError("Heart rate range must be in 'min-max' format (e.g., '60-120')")


def generate_activity_pattern_data(pattern: str, count: int) -> List[int]:
    """Generate activity levels based on pattern."""
    if pattern == "resting":
        return [0] * count
    elif pattern == "walk":
        return [1] * count
    elif pattern == "play":
        return [2] * count
    elif pattern == "mixed":
        # Mixed pattern with realistic distribution
        return random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2], k=count)
    else:
        raise ValueError(f"Unknown activity pattern: {pattern}")


def generate_gps_walk(start_lon: float, start_lat: float, count: int) -> List[tuple[float, float]]:
    """Generate a random walk starting from given coordinates."""
    coordinates = [(start_lon, start_lat)]
    
    # Approximate scale: 0.0001 degrees ≈ 10 meters
    max_step = 0.0001  # Small random walk steps
    
    current_lon, current_lat = start_lon, start_lat
    
    for _ in range(count - 1):
        # Random walk with small steps
        lon_step = random.uniform(-max_step, max_step)
        lat_step = random.uniform(-max_step, max_step)
        
        current_lon += lon_step
        current_lat += lat_step
        
        coordinates.append((current_lon, current_lat))
    
    return coordinates


def generate_heart_rate(activity_level: int, hr_min: int, hr_max: int) -> int:
    """Generate heart rate based on activity level and range."""
    range_size = hr_max - hr_min
    
    if activity_level == 0:  # resting
        # Lower third of the range
        return random.randint(hr_min, hr_min + range_size // 3)
    elif activity_level == 1:  # walk
        # Middle third of the range
        mid_start = hr_min + range_size // 3
        mid_end = hr_min + 2 * range_size // 3
        return random.randint(mid_start, mid_end)
    else:  # play (activity_level == 2)
        # Upper third of the range
        return random.randint(hr_min + 2 * range_size // 3, hr_max)


def generate_samples(
    collar_id: str,
    count: int,
    seed: int = None,
    hr_range: tuple[int, int] = (60, 120),
    activity_pattern: str = "mixed",
    start_geo: tuple[float, float] = (-74.0060, 40.7128),
    start_time: datetime = None
) -> List[Dict[str, Any]]:
    """Generate N telemetry samples with specified parameters."""
    
    if seed is not None:
        random.seed(seed)
    
    if start_time is None:
        start_time = datetime.now(timezone.utc)
    
    # Generate activity levels for all samples
    activity_levels = generate_activity_pattern_data(activity_pattern, count)
    
    # Generate GPS coordinates
    coordinates = generate_gps_walk(start_geo[0], start_geo[1], count)
    
    samples = []
    hr_min, hr_max = hr_range
    
    for i in range(count):
        # Calculate timestamp with 30-second intervals
        timestamp = start_time + timedelta(seconds=i * 30)
        
        # Generate heart rate based on activity level
        heart_rate = generate_heart_rate(activity_levels[i], hr_min, hr_max)
        
        # Get GPS coordinates for this sample
        lon, lat = coordinates[i]
        
        sample = {
            "collar_id": collar_id,
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "heart_rate": heart_rate,
            "activity_level": activity_levels[i],
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        
        samples.append(sample)
    
    return samples


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic telemetry samples for testing",
        epilog="Example: %(prog)s --collar-id SN-1234 --count 10 --seed 42"
    )
    
    parser.add_argument(
        "--collar-id",
        required=True,
        help="Collar identifier (e.g., 'SN-1A4B7C-9Z')"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of samples to generate (default: 10)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for deterministic generation"
    )
    
    parser.add_argument(
        "--hr-range",
        default="60-120",
        help="Heart rate range as 'min-max' (default: '60-120')"
    )
    
    parser.add_argument(
        "--activity-pattern",
        choices=["resting", "walk", "play", "mixed"],
        default="mixed",
        help="Activity pattern to generate (default: mixed)"
    )
    
    parser.add_argument(
        "--start-geo",
        default="-74.0060,40.7128",
        help="Starting GPS coordinates as 'lon,lat' (default: '-74.0060,40.7128')"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)"
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse arguments
        hr_range = parse_hr_range(args.hr_range)
        start_geo = parse_geo_coordinates(args.start_geo)
        
        # Validate count
        if args.count <= 0:
            raise ValueError("Count must be positive")
        if args.count > 10000:
            raise ValueError("Count too large (max: 10000)")
        
        # Generate samples
        samples = generate_samples(
            collar_id=args.collar_id,
            count=args.count,
            seed=args.seed,
            hr_range=hr_range,
            activity_pattern=args.activity_pattern,
            start_geo=start_geo
        )
        
        # Format output
        if args.pretty:
            output = json.dumps(samples, indent=2)
        else:
            output = json.dumps(samples)
        
        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Generated {len(samples)} samples to {args.output}", file=sys.stderr)
        else:
            print(output)
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())