#!/usr/bin/env python3
"""
Deterministic Telemetry Sample Generator for Petty

This script generates consistent, reproducible telemetry data samples
that can be referenced in consumer documentation and used for testing.

Usage:
    python tools/generate_telemetry_samples.py --samples 100 --output samples.jsonl
    python tools/generate_telemetry_samples.py --format csv --collar-id SN-TEST-001
    python tools/generate_telemetry_samples.py --scenario active_day
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union


class DeterministicTelemetryGenerator:
    """Generates deterministic telemetry data for documentation and testing."""
    
    def __init__(self, seed: int = 42):
        """Initialize with a fixed seed for reproducibility."""
        import random
        self.random = random.Random(seed)
        
        # Pre-defined behavior patterns for realistic simulation
        self.behavior_patterns = {
            'sleeping': {
                'activity_level': 0,
                'heart_rate_range': (60, 75),
                'temperature_range': (37.8, 38.2),
                'movement_variance': 0.02
            },
            'resting': {
                'activity_level': 0,
                'heart_rate_range': (70, 85),
                'temperature_range': (38.0, 38.5),
                'movement_variance': 0.05
            },
            'walking': {
                'activity_level': 1,
                'heart_rate_range': (90, 110),
                'temperature_range': (38.2, 38.8),
                'movement_variance': 0.15
            },
            'playing': {
                'activity_level': 2,
                'heart_rate_range': (120, 150),
                'temperature_range': (38.5, 39.2),
                'movement_variance': 0.35
            }
        }
    
    def generate_sample(
        self,
        collar_id: str,
        timestamp: datetime,
        behavior: str = 'auto',
        base_location: tuple[float, float] = (-74.0060, 40.7128)  # NYC coordinates
    ) -> Dict:
        """Generate a single telemetry sample."""
        
        # Auto-select behavior based on time of day for realism
        if behavior == 'auto':
            hour = timestamp.hour
            if 0 <= hour < 6 or 22 <= hour < 24:
                behavior = 'sleeping'
            elif 6 <= hour < 8 or 18 <= hour < 22:
                behavior = 'resting'
            elif 8 <= hour < 12 or 14 <= hour < 18:
                behavior = self.random.choice(['walking', 'playing', 'resting'])
            else:  # 12-14 (afternoon rest)
                behavior = 'resting'
        
        pattern = self.behavior_patterns[behavior]
        
        # Generate physiological data
        heart_rate = self.random.randint(*pattern['heart_rate_range'])
        temperature = round(
            self.random.uniform(*pattern['temperature_range']), 1
        )
        
        # Generate accelerometer data with pattern-based variance
        variance = pattern['movement_variance']
        accel = {
            'x': round(self.random.uniform(-variance, variance), 3),
            'y': round(self.random.uniform(-variance, variance), 3),
            'z': round(0.98 + self.random.uniform(-0.02, 0.02), 3)  # Gravity baseline
        }
        
        # Generate location with small random walk
        lon_offset = self.random.uniform(-0.001, 0.001)
        lat_offset = self.random.uniform(-0.001, 0.001)
        location = {
            'type': 'Point',
            'coordinates': [
                round(base_location[0] + lon_offset, 6),
                round(base_location[1] + lat_offset, 6)
            ]
        }
        
        # Generate battery level (slow decline over time)
        base_battery = 100 - (timestamp.hour * 2)  # Rough daily decline
        battery_noise = self.random.randint(-5, 2)
        battery_pct = max(10, min(100, base_battery + battery_noise))
        
        return {
            'device_id': collar_id,
            'timestamp': timestamp.isoformat(),
            'metrics': {
                'accel': accel,
                'activity_score': self._calculate_activity_score(accel, pattern['activity_level']),
                'resting_heart_rate_proxy': heart_rate,
                'temperature_c': temperature
            },
            'location': location,
            'battery_pct': battery_pct,
            'firmware_version': '1.4.2',
            'seq': self.random.randint(10000, 99999),
            '_behavior_hint': behavior  # For documentation purposes
        }
    
    def _calculate_activity_score(self, accel: Dict[str, float], base_level: int) -> int:
        """Calculate activity score based on accelerometer data."""
        magnitude = (accel['x']**2 + accel['y']**2 + (accel['z']-0.98)**2) ** 0.5
        score = int(magnitude * 1000) + (base_level * 20)
        return min(100, max(0, score))
    
    def generate_scenario(self, collar_id: str, scenario: str, start_time: datetime, count: int) -> List[Dict]:
        """Generate samples for predefined scenarios."""
        samples = []
        
        if scenario == 'active_day':
            behaviors = ['sleeping'] * 6 + ['resting'] * 2 + ['walking'] * 4 + \
                       ['resting'] * 2 + ['playing'] * 4 + ['walking'] * 4 + \
                       ['resting'] * 2
        elif scenario == 'quiet_day':
            behaviors = ['sleeping'] * 8 + ['resting'] * 12 + ['walking'] * 4
        elif scenario == 'playful_day':
            behaviors = ['sleeping'] * 6 + ['playing'] * 8 + ['walking'] * 6 + \
                       ['resting'] * 4
        else:
            behaviors = ['auto'] * count
        
        for i in range(count):
            timestamp = start_time + timedelta(minutes=i * 5)  # 5-minute intervals
            behavior = behaviors[i % len(behaviors)] if behaviors else 'auto'
            
            sample = self.generate_sample(
                collar_id=collar_id,
                timestamp=timestamp,
                behavior=behavior
            )
            samples.append(sample)
        
        return samples
    
    def export_samples(
        self,
        samples: List[Dict],
        output_file: Path,
        format_type: str = 'jsonl'
    ) -> None:
        """Export samples to specified format."""
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == 'jsonl':
            with open(output_file, 'w') as f:
                for sample in samples:
                    f.write(json.dumps(sample) + '\n')
        
        elif format_type == 'json':
            with open(output_file, 'w') as f:
                json.dump(samples, f, indent=2)
        
        elif format_type == 'csv':
            if not samples:
                return
            
            # Flatten nested structures for CSV
            flattened_samples = []
            for sample in samples:
                flat = {
                    'device_id': sample['device_id'],
                    'timestamp': sample['timestamp'],
                    'accel_x': sample['metrics']['accel']['x'],
                    'accel_y': sample['metrics']['accel']['y'],
                    'accel_z': sample['metrics']['accel']['z'],
                    'activity_score': sample['metrics']['activity_score'],
                    'heart_rate': sample['metrics']['resting_heart_rate_proxy'],
                    'temperature_c': sample['metrics']['temperature_c'],
                    'longitude': sample['location']['coordinates'][0],
                    'latitude': sample['location']['coordinates'][1],
                    'battery_pct': sample['battery_pct'],
                    'firmware_version': sample['firmware_version'],
                    'seq': sample['seq'],
                    'behavior_hint': sample.get('_behavior_hint', 'unknown')
                }
                flattened_samples.append(flat)
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_samples[0].keys())
                writer.writeheader()
                writer.writerows(flattened_samples)
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate deterministic telemetry samples for Petty',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--collar-id', '-c',
        default='SN-SAMPLE-001',
        help='Collar device ID (default: %(default)s)'
    )
    
    parser.add_argument(
        '--samples', '-n',
        type=int,
        default=24,
        help='Number of samples to generate (default: %(default)s)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('docs/samples/telemetry_samples.jsonl'),
        help='Output file path (default: %(default)s)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['jsonl', 'json', 'csv'],
        default='jsonl',
        help='Output format (default: %(default)s)'
    )
    
    parser.add_argument(
        '--scenario',
        choices=['active_day', 'quiet_day', 'playful_day', 'auto'],
        default='auto',
        help='Behavior scenario to simulate (default: %(default)s)'
    )
    
    parser.add_argument(
        '--start-time',
        type=lambda s: datetime.fromisoformat(s),
        default=datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc),
        help='Start timestamp (ISO format, default: 2025-01-15T00:00:00+00:00)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: %(default)s)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        generator = DeterministicTelemetryGenerator(seed=args.seed)
        
        if args.verbose:
            print(f"Generating {args.samples} samples for {args.collar_id}")
            print(f"Scenario: {args.scenario}")
            print(f"Start time: {args.start_time}")
            print(f"Output: {args.output} ({args.format})")
        
        if args.scenario == 'auto':
            samples = []
            for i in range(args.samples):
                timestamp = args.start_time + timedelta(minutes=i * 5)
                sample = generator.generate_sample(
                    collar_id=args.collar_id,
                    timestamp=timestamp
                )
                samples.append(sample)
        else:
            samples = generator.generate_scenario(
                collar_id=args.collar_id,
                scenario=args.scenario,
                start_time=args.start_time,
                count=args.samples
            )
        
        generator.export_samples(samples, args.output, args.format)
        
        print(f"✅ Generated {len(samples)} samples successfully!")
        print(f"   Output: {args.output}")
        print(f"   Format: {args.format}")
        
        if args.verbose:
            print("\nSample preview:")
            for i, sample in enumerate(samples[:3]):
                print(f"  {i+1}: {sample['timestamp']} - {sample.get('_behavior_hint', 'auto')} - Activity: {sample['metrics']['activity_score']}")
            if len(samples) > 3:
                print(f"  ... and {len(samples) - 3} more")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())