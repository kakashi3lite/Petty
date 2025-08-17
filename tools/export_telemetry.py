#!/usr/bin/env python3
"""
Privacy-friendly telemetry export script for Petty collar data.

Exports telemetry data in CSV or JSONL format with configurable GPS precision
for privacy protection.
"""

import argparse
import csv
import json
import random
import sys
from datetime import datetime, timedelta
from typing import Any


def round_gps_coordinates(coordinates: list[float], precision: int = 4) -> list[float]:
    """
    Round GPS coordinates to specified decimal precision for privacy.
    
    Args:
        coordinates: [longitude, latitude] pair
        precision: Number of decimal places (default 4 for ~11m accuracy)
        
    Returns:
        Rounded coordinates list
    """
    MIN_COORDINATES = 2
    if len(coordinates) < MIN_COORDINATES:
        return coordinates

    return [round(coordinates[0], precision), round(coordinates[1], precision)]


def generate_stub_telemetry(
    collar_id: str,
    start_date: datetime,
    end_date: datetime,
    interval_minutes: int = 10
) -> list[dict[str, Any]]:
    """
    Generate stub telemetry data for testing/demo purposes.
    Based on the timeline_generator stub logic.
    
    Args:
        collar_id: Collar identifier
        start_date: Start of data range
        end_date: End of data range
        interval_minutes: Data point interval in minutes
        
    Returns:
        List of telemetry data points
    """
    data = []
    current_time = start_date

    # Starting location (NYC coordinates from existing code)
    lon, lat = -74.0060, 40.7128

    while current_time <= end_date:
        # Generate realistic activity level (weighted distribution)
        activity_level = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]

        # Generate heart rate based on activity
        base_hr = 60
        activity_modifier = 0 if activity_level == 0 else 20 if activity_level == 1 else 50
        heart_rate = base_hr + activity_modifier + random.randint(-5, 5)

        # Generate slight location movement (more if active)
        movement_factor = 1 if activity_level else 0.2
        lon += random.uniform(-0.0003, 0.0003) * movement_factor
        lat += random.uniform(-0.0003, 0.0003) * movement_factor

        data_point = {
            "collar_id": collar_id,
            "timestamp": current_time.isoformat() + "Z",
            "heart_rate": heart_rate,
            "activity_level": activity_level,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }

        data.append(data_point)
        current_time += timedelta(minutes=interval_minutes)

    return data


def apply_privacy_filter(
    data: list[dict[str, Any]],
    full_geo: bool = False
) -> list[dict[str, Any]]:
    """
    Apply privacy filtering to telemetry data.
    
    Args:
        data: Raw telemetry data
        full_geo: If True, preserve full GPS precision
        
    Returns:
        Privacy-filtered data
    """
    filtered_data = []

    for point in data:
        filtered_point = point.copy()

        # Apply GPS rounding for privacy unless full_geo is requested
        if not full_geo and "location" in filtered_point:
            location = filtered_point["location"]
            if "coordinates" in location:
                location["coordinates"] = round_gps_coordinates(
                    location["coordinates"], precision=4
                )

        filtered_data.append(filtered_point)

    return filtered_data


def export_to_csv(data: list[dict[str, Any]], output_path: str) -> None:
    """
    Export telemetry data to CSV format.
    
    Args:
        data: Telemetry data to export
        output_path: Output file path
    """
    if not data:
        # Create empty CSV with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['collar_id', 'timestamp', 'heart_rate', 'activity_level', 'longitude', 'latitude']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        return

    # Define field order for consistency
    fieldnames = ['collar_id', 'timestamp', 'heart_rate', 'activity_level', 'longitude', 'latitude']

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for point in data:
            # Flatten location coordinates for CSV
            row = {
                'collar_id': point.get('collar_id', ''),
                'timestamp': point.get('timestamp', ''),
                'heart_rate': point.get('heart_rate', ''),
                'activity_level': point.get('activity_level', ''),
                'longitude': '',
                'latitude': ''
            }

            # Extract coordinates
            location = point.get('location', {})
            coordinates = location.get('coordinates', [])
            MIN_COORDINATES = 2
            if len(coordinates) >= MIN_COORDINATES:
                row['longitude'] = coordinates[0]
                row['latitude'] = coordinates[1]

            writer.writerow(row)


def export_to_jsonl(data: list[dict[str, Any]], output_path: str) -> None:
    """
    Export telemetry data to JSON Lines format.
    
    Args:
        data: Telemetry data to export
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        for point in data:
            json.dump(point, jsonfile, separators=(',', ':'))
            jsonfile.write('\n')


def parse_date(date_str: str) -> datetime:
    """
    Parse date string in ISO format.
    
    Args:
        date_str: Date string (YYYY-MM-DD or ISO format)
        
    Returns:
        Parsed datetime object
    """
    # Try different formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Invalid date format: {date_str}")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Export collar telemetry data with privacy controls',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s --collar-id SN-123 --start 2025-01-01 --end 2025-01-02 --format csv --out data.csv
  %(prog)s --collar-id SN-456 --start 2025-01-01T00:00:00 --end 2025-01-01T23:59:59 --format jsonl --out data.jsonl --full-geo
        '''
    )

    parser.add_argument(
        '--collar-id', '-c',
        required=True,
        help='Collar identifier to export data for'
    )

    parser.add_argument(
        '--start', '-s',
        required=True,
        help='Start date/time (YYYY-MM-DD or ISO format)'
    )

    parser.add_argument(
        '--end', '-e',
        required=True,
        help='End date/time (YYYY-MM-DD or ISO format)'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['csv', 'jsonl'],
        default='csv',
        help='Output format (default: csv)'
    )

    parser.add_argument(
        '--out', '-o',
        required=True,
        help='Output file path'
    )

    parser.add_argument(
        '--full-geo',
        action='store_true',
        help='Include full GPS precision (default: rounded to 4 decimals for privacy)'
    )

    args = parser.parse_args()

    try:
        # Parse date arguments
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)

        if start_date >= end_date:
            print("Error: Start date must be before end date", file=sys.stderr)
            return 1

        # Generate telemetry data (in production, this would query real endpoints)
        print(f"Retrieving telemetry data for collar {args.collar_id} from {start_date} to {end_date}...")
        raw_data = generate_stub_telemetry(args.collar_id, start_date, end_date)

        # Apply privacy filtering
        filtered_data = apply_privacy_filter(raw_data, full_geo=args.full_geo)

        # Export data
        print(f"Exporting {len(filtered_data)} data points to {args.out} in {args.format} format...")

        if args.format == 'csv':
            export_to_csv(filtered_data, args.out)
        elif args.format == 'jsonl':
            export_to_jsonl(filtered_data, args.out)

        privacy_note = "full precision" if args.full_geo else "4-decimal privacy rounding"
        print(f"Export complete. GPS coordinates exported with {privacy_note}.")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
