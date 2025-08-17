"""
Unit tests for the telemetry export script.
Tests CSV/JSONL writers, GPS rounding, and column order.
"""

import csv
import json
import os
import sys
import tempfile
from datetime import datetime
from typing import Any

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from export_telemetry import (
    apply_privacy_filter,
    export_to_csv,
    export_to_jsonl,
    generate_stub_telemetry,
    parse_date,
    round_gps_coordinates,
)


class TestGPSRounding:
    """Test GPS coordinate rounding functionality."""

    def test_round_gps_coordinates_default_precision(self):
        """Test default 4-decimal precision rounding."""
        coords = [-74.00612345678, 40.71283456789]
        rounded = round_gps_coordinates(coords)

        assert rounded == [-74.0061, 40.7128]
        assert len(str(rounded[0]).split('.')[1]) <= 4
        assert len(str(rounded[1]).split('.')[1]) <= 4

    def test_round_gps_coordinates_custom_precision(self):
        """Test custom precision rounding."""
        coords = [-74.00612345678, 40.71283456789]

        # Test 2-decimal precision
        rounded = round_gps_coordinates(coords, precision=2)
        assert rounded == [-74.01, 40.71]

        # Test 6-decimal precision
        rounded = round_gps_coordinates(coords, precision=6)
        assert rounded == [-74.006123, 40.712835]

    def test_round_gps_coordinates_edge_cases(self):
        """Test edge cases for GPS rounding."""
        # Empty coordinates
        assert round_gps_coordinates([]) == []

        # Single coordinate
        assert round_gps_coordinates([-74.123456]) == [-74.123456]

        # Exact values
        assert round_gps_coordinates([-74.0000, 40.0000]) == [-74.0, 40.0]

        # Already rounded values
        assert round_gps_coordinates([-74.1234, 40.5678]) == [-74.1234, 40.5678]


class TestPrivacyFilter:
    """Test privacy filtering functionality."""

    def create_sample_data(self) -> list[dict[str, Any]]:
        """Create sample telemetry data for testing."""
        return [
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:00:00Z",
                "heart_rate": 75,
                "activity_level": 1,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.00612345678, 40.71283456789]
                }
            },
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:10:00Z",
                "heart_rate": 80,
                "activity_level": 0,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.00598765432, 40.71297654321]
                }
            }
        ]

    def test_privacy_filter_default_rounding(self):
        """Test default privacy filtering with GPS rounding."""
        data = self.create_sample_data()
        filtered = apply_privacy_filter(data, full_geo=False)

        # Check that coordinates are rounded
        assert filtered[0]["location"]["coordinates"] == [-74.0061, 40.7128]
        assert filtered[1]["location"]["coordinates"] == [-74.006, 40.713]

        # Check other data remains unchanged
        assert filtered[0]["collar_id"] == "SN-123"
        assert filtered[0]["heart_rate"] == 75

    def test_privacy_filter_full_geo(self):
        """Test privacy filtering with full GPS precision."""
        data = self.create_sample_data()
        filtered = apply_privacy_filter(data, full_geo=True)

        # Check that coordinates are NOT rounded
        assert filtered[0]["location"]["coordinates"] == [-74.00612345678, 40.71283456789]
        assert filtered[1]["location"]["coordinates"] == [-74.00598765432, 40.71297654321]

    def test_privacy_filter_missing_location(self):
        """Test privacy filtering with missing location data."""
        data = [
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:00:00Z",
                "heart_rate": 75,
                "activity_level": 1
                # No location field
            }
        ]

        filtered = apply_privacy_filter(data, full_geo=False)
        assert len(filtered) == 1
        assert "location" not in filtered[0]


class TestCSVExport:
    """Test CSV export functionality."""

    def create_sample_data(self) -> list[dict[str, Any]]:
        """Create sample telemetry data for testing."""
        return [
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:00:00Z",
                "heart_rate": 75,
                "activity_level": 1,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.0061, 40.7128]
                }
            },
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:10:00Z",
                "heart_rate": 80,
                "activity_level": 0,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.006, 40.713]
                }
            }
        ]

    def test_csv_export_column_order(self):
        """Test that CSV export maintains correct column order."""
        data = self.create_sample_data()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv(data, output_path)

            with open(output_path) as f:
                reader = csv.reader(f)
                headers = next(reader)

                # Check column order
                expected_headers = ['collar_id', 'timestamp', 'heart_rate', 'activity_level', 'longitude', 'latitude']
                assert headers == expected_headers

                # Check first data row
                first_row = next(reader)
                assert first_row[0] == "SN-123"  # collar_id
                assert first_row[1] == "2025-01-01T10:00:00Z"  # timestamp
                assert first_row[2] == "75"  # heart_rate
                assert first_row[3] == "1"  # activity_level
                assert first_row[4] == "-74.0061"  # longitude
                assert first_row[5] == "40.7128"  # latitude

        finally:
            os.unlink(output_path)

    def test_csv_export_coordinate_flattening(self):
        """Test that GPS coordinates are properly flattened in CSV."""
        data = self.create_sample_data()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv(data, output_path)

            with open(output_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 2

                # Check coordinate flattening
                assert rows[0]['longitude'] == '-74.0061'
                assert rows[0]['latitude'] == '40.7128'
                assert rows[1]['longitude'] == '-74.006'
                assert rows[1]['latitude'] == '40.713'

        finally:
            os.unlink(output_path)

    def test_csv_export_empty_data(self):
        """Test CSV export with empty data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv([], output_path)

            with open(output_path) as f:
                reader = csv.reader(f)
                headers = next(reader)

                # Should have headers even with no data
                expected_headers = ['collar_id', 'timestamp', 'heart_rate', 'activity_level', 'longitude', 'latitude']
                assert headers == expected_headers

                # Should have no data rows
                rows = list(reader)
                assert len(rows) == 0

        finally:
            os.unlink(output_path)

    def test_csv_export_missing_coordinates(self):
        """Test CSV export with missing coordinate data."""
        data = [
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:00:00Z",
                "heart_rate": 75,
                "activity_level": 1,
                "location": {
                    "type": "Point"
                    # Missing coordinates
                }
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv(data, output_path)

            with open(output_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]['longitude'] == ''
                assert rows[0]['latitude'] == ''

        finally:
            os.unlink(output_path)


class TestJSONLExport:
    """Test JSONL export functionality."""

    def create_sample_data(self) -> list[dict[str, Any]]:
        """Create sample telemetry data for testing."""
        return [
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:00:00Z",
                "heart_rate": 75,
                "activity_level": 1,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.0061, 40.7128]
                }
            },
            {
                "collar_id": "SN-123",
                "timestamp": "2025-01-01T10:10:00Z",
                "heart_rate": 80,
                "activity_level": 0,
                "location": {
                    "type": "Point",
                    "coordinates": [-74.006, 40.713]
                }
            }
        ]

    def test_jsonl_export_format(self):
        """Test that JSONL export creates valid JSON Lines format."""
        data = self.create_sample_data()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            output_path = f.name

        try:
            export_to_jsonl(data, output_path)

            with open(output_path) as f:
                lines = f.readlines()

                assert len(lines) == 2

                # Each line should be valid JSON
                for line in lines:
                    json_data = json.loads(line.strip())
                    assert isinstance(json_data, dict)

                # Check first record
                first_record = json.loads(lines[0].strip())
                assert first_record["collar_id"] == "SN-123"
                assert first_record["heart_rate"] == 75
                assert first_record["location"]["coordinates"] == [-74.0061, 40.7128]

        finally:
            os.unlink(output_path)

    def test_jsonl_export_preserves_structure(self):
        """Test that JSONL export preserves original data structure."""
        data = self.create_sample_data()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            output_path = f.name

        try:
            export_to_jsonl(data, output_path)

            with open(output_path) as f:
                lines = f.readlines()

                # Load both records
                records = [json.loads(line.strip()) for line in lines]

                # Check structure preservation
                for i, record in enumerate(records):
                    original = data[i]

                    assert record["collar_id"] == original["collar_id"]
                    assert record["timestamp"] == original["timestamp"]
                    assert record["heart_rate"] == original["heart_rate"]
                    assert record["activity_level"] == original["activity_level"]
                    assert record["location"]["type"] == original["location"]["type"]
                    assert record["location"]["coordinates"] == original["location"]["coordinates"]

        finally:
            os.unlink(output_path)

    def test_jsonl_export_empty_data(self):
        """Test JSONL export with empty data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            output_path = f.name

        try:
            export_to_jsonl([], output_path)

            with open(output_path) as f:
                content = f.read()
                assert content == ""

        finally:
            os.unlink(output_path)


class TestDateParsing:
    """Test date parsing functionality."""

    def test_parse_date_formats(self):
        """Test parsing of various date formats."""
        # Basic date format
        date1 = parse_date("2025-01-01")
        assert date1 == datetime(2025, 1, 1)

        # Date with time
        date2 = parse_date("2025-01-01T10:30:00")
        assert date2 == datetime(2025, 1, 1, 10, 30, 0)

        # Date with time and Z timezone
        date3 = parse_date("2025-01-01T10:30:00Z")
        assert date3 == datetime(2025, 1, 1, 10, 30, 0)

    def test_parse_date_invalid_format(self):
        """Test error handling for invalid date formats."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("invalid-date")

        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("2025/01/01")


class TestStubDataGeneration:
    """Test stub telemetry data generation."""

    def test_generate_stub_telemetry_basic(self):
        """Test basic stub data generation."""
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 30, 0)

        data = generate_stub_telemetry("SN-123", start, end, interval_minutes=10)

        # Should have 4 data points (10:00, 10:10, 10:20, 10:30)
        assert len(data) == 4

        # Check data structure
        for point in data:
            assert "collar_id" in point
            assert "timestamp" in point
            assert "heart_rate" in point
            assert "activity_level" in point
            assert "location" in point

            assert point["collar_id"] == "SN-123"
            assert isinstance(point["heart_rate"], int)
            assert point["activity_level"] in [0, 1, 2]
            assert point["location"]["type"] == "Point"
            assert len(point["location"]["coordinates"]) == 2

    def test_generate_stub_telemetry_heart_rate_ranges(self):
        """Test that heart rates are within expected ranges."""
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 11, 0, 0)

        data = generate_stub_telemetry("SN-123", start, end)

        for point in data:
            hr = point["heart_rate"]
            activity = point["activity_level"]

            # Heart rates should be reasonable for dogs
            assert 50 <= hr <= 170  # Broad range accounting for activity levels

            # Higher activity should generally correlate with higher heart rates
            if activity == 0:
                assert 50 <= hr <= 70  # Resting range
            elif activity == 2:
                assert 100 <= hr <= 170  # High activity range


if __name__ == "__main__":
    pytest.main([__file__])
