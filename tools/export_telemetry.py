#!/usr/bin/env python3
"""
Privacy Export Script for Petty Pet Monitoring System

Exports telemetry data with privacy controls:
- Default: round GPS to 4 decimals for privacy
- --full-geo: disable rounding (use full precision)
- Support for JSONL and CSV output formats
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def round_coordinates(coordinates: List[float], precision: int = 4) -> List[float]:
    """Round GPS coordinates to specified decimal places for privacy."""
    return [round(coord, precision) for coord in coordinates]


def format_timestamp_iso(timestamp_str: str) -> str:
    """Ensure timestamp is in ISO format."""
    # Handle various timestamp formats and normalize to ISO
    try:
        if timestamp_str.endswith('Z'):
            return timestamp_str
        # Try to parse and reformat if needed
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        return timestamp_str  # Return as-is if can't parse


def apply_privacy_filters(data: Dict[str, Any], full_geo: bool = False) -> Dict[str, Any]:
    """Apply privacy filters to telemetry data."""
    filtered_data = data.copy()
    
    # Apply GPS coordinate precision limiting unless full-geo is enabled
    if not full_geo and 'location' in filtered_data:
        location = filtered_data['location']
        if isinstance(location, dict) and 'coordinates' in location:
            coordinates = location['coordinates']
            if isinstance(coordinates, list) and len(coordinates) >= 2:
                filtered_data['location'] = {
                    **location,
                    'coordinates': round_coordinates(coordinates)
                }
    
    # Ensure timestamp is properly formatted
    if 'timestamp' in filtered_data:
        filtered_data['timestamp'] = format_timestamp_iso(filtered_data['timestamp'])
    
    return filtered_data


def write_jsonl(data: List[Dict[str, Any]], output_file: str) -> None:
    """Write data to JSONL format."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in data:
            json.dump(record, f, separators=(',', ':'))
            f.write('\n')


def write_csv(data: List[Dict[str, Any]], output_file: str) -> None:
    """Write data to CSV format."""
    if not data:
        # Create empty CSV file
        with open(output_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['collar_id', 'timestamp', 'heart_rate', 'activity_level', 'longitude', 'latitude'])
        return
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        # Flatten the data structure for CSV
        fieldnames = ['collar_id', 'timestamp', 'heart_rate', 'activity_level', 'longitude', 'latitude']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for record in data:
            row = {
                'collar_id': record.get('collar_id', ''),
                'timestamp': record.get('timestamp', ''),
                'heart_rate': record.get('heart_rate', ''),
                'activity_level': record.get('activity_level', ''),
                'longitude': '',
                'latitude': ''
            }
            
            # Extract coordinates from GeoJSON structure
            location = record.get('location', {})
            if isinstance(location, dict) and 'coordinates' in location:
                coords = location['coordinates']
                if isinstance(coords, list) and len(coords) >= 2:
                    row['longitude'] = coords[0]
                    row['latitude'] = coords[1]
            
            writer.writerow(row)


def load_sample_data(collar_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Load sample telemetry data for the given parameters.
    
    In a real implementation, this would query a database or data store.
    For now, we'll generate some sample data for demonstration.
    """
    # Generate sample data for demonstration
    sample_data = [
        {
            "collar_id": collar_id,
            "timestamp": "2025-08-17T12:30:05Z",
            "heart_rate": 75,
            "activity_level": 1,
            "location": {"type": "Point", "coordinates": [-74.006000123456, 40.712800987654]}
        },
        {
            "collar_id": collar_id,
            "timestamp": "2025-08-17T12:35:05Z",
            "heart_rate": 82,
            "activity_level": 2,
            "location": {"type": "Point", "coordinates": [-74.006100234567, 40.712900876543]}
        }
    ]
    
    # Filter by date range (simplified for demo)
    # In real implementation, this would be a proper database query
    return sample_data


def validate_collar_id(collar_id: str) -> None:
    """Validate collar ID format."""
    import re
    pattern = re.compile(r'^[A-Z]{2}-\d{3,6}$')
    if not pattern.match(collar_id):
        raise ValueError(f"Invalid collar ID format '{collar_id}'. Expected format: XX-123 (2 letters, dash, 3-6 digits)")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Export telemetry data with privacy controls',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --collar-id SN-123 --start 2025-01-01 --end 2025-01-02 --format jsonl --out data.jsonl
  %(prog)s --collar-id SN-456 --start 2025-01-01 --end 2025-01-02 --format csv --out data.csv --full-geo
        """
    )
    
    parser.add_argument(
        '--collar-id', '-c',
        required=True,
        help='Collar ID to export data for (e.g., SN-123)'
    )
    parser.add_argument(
        '--start', '-s',
        required=True,
        help='Start date for export (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)'
    )
    parser.add_argument(
        '--end', '-e',
        required=True,
        help='End date for export (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['jsonl', 'csv'],
        default='jsonl',
        help='Output format (default: jsonl)'
    )
    parser.add_argument(
        '--out', '-o',
        required=True,
        help='Output file path'
    )
    parser.add_argument(
        '--full-geo',
        action='store_true',
        help='Disable GPS coordinate rounding (preserve full precision)'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate collar ID format
        validate_collar_id(args.collar_id)
        
        # Load telemetry data
        print(f"Loading telemetry data for collar {args.collar_id} from {args.start} to {args.end}...", file=sys.stderr)
        raw_data = load_sample_data(args.collar_id, args.start, args.end)
        
        # Apply privacy filters
        filtered_data = [apply_privacy_filters(record, args.full_geo) for record in raw_data]
        
        # Export data
        if args.format == 'jsonl':
            write_jsonl(filtered_data, args.out)
        elif args.format == 'csv':
            write_csv(filtered_data, args.out)
        
        precision_note = "full precision" if args.full_geo else "4 decimal places"
        print(f"Exported {len(filtered_data)} records to {args.out} ({args.format.upper()}, GPS: {precision_note})", file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())