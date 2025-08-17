#!/usr/bin/env python3
"""
Tests for privacy export and telemetry sample generation tools.

These tests validate:
- CSV/JSONL writer functionality
- Deterministic sampling with seed
- Privacy controls for GPS precision
- Input validation and error handling
"""

import json
import csv
import tempfile
import os
from typing import Dict, List, Any
import pytest

# Import the tools modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

try:
    import export_telemetry
    import generate_samples
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"Tools not available: {e}")
    TOOLS_AVAILABLE = False


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="Tools not available")
class TestExportTelemetry:
    """Test the export_telemetry.py functionality."""
    
    def test_round_coordinates_default_precision(self):
        """Test GPS coordinate rounding to 4 decimal places."""
        coords = [-74.006000123456, 40.712800987654]
        rounded = export_telemetry.round_coordinates(coords)
        assert rounded == [-74.006, 40.7128]
    
    def test_round_coordinates_custom_precision(self):
        """Test GPS coordinate rounding to custom precision."""
        coords = [-74.006000123456, 40.712800987654]
        rounded = export_telemetry.round_coordinates(coords, precision=2)
        assert rounded == [-74.01, 40.71]
    
    def test_apply_privacy_filters_default(self):
        """Test privacy filter application with default settings."""
        data = {
            "collar_id": "SN-123",
            "timestamp": "2025-08-17T12:30:05Z",
            "heart_rate": 75,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006000123456, 40.712800987654]
            }
        }
        
        filtered = export_telemetry.apply_privacy_filters(data)
        
        # Should round coordinates to 4 decimal places
        assert filtered["location"]["coordinates"] == [-74.006, 40.7128]
        # Other fields should remain unchanged
        assert filtered["collar_id"] == "SN-123"
        assert filtered["heart_rate"] == 75
    
    def test_apply_privacy_filters_full_geo(self):
        """Test privacy filter with full geo precision enabled."""
        data = {
            "collar_id": "SN-123",
            "timestamp": "2025-08-17T12:30:05Z",
            "heart_rate": 75,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.006000123456, 40.712800987654]
            }
        }
        
        filtered = export_telemetry.apply_privacy_filters(data, full_geo=True)
        
        # Should preserve full precision
        assert filtered["location"]["coordinates"] == [-74.006000123456, 40.712800987654]
    
    def test_write_jsonl(self):
        """Test JSONL file writing."""
        test_data = [
            {"collar_id": "SN-123", "heart_rate": 75},
            {"collar_id": "SN-124", "heart_rate": 82}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
            temp_path = f.name
        
        try:
            export_telemetry.write_jsonl(test_data, temp_path)
            
            # Read back and verify
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2
            assert json.loads(lines[0]) == {"collar_id": "SN-123", "heart_rate": 75}
            assert json.loads(lines[1]) == {"collar_id": "SN-124", "heart_rate": 82}
            
        finally:
            os.unlink(temp_path)
    
    def test_write_csv(self):
        """Test CSV file writing."""
        test_data = [
            {
                "collar_id": "SN-123",
                "timestamp": "2025-08-17T12:30:05Z",
                "heart_rate": 75,
                "activity_level": 1,
                "location": {"type": "Point", "coordinates": [-74.006, 40.7128]}
            },
            {
                "collar_id": "SN-124",
                "timestamp": "2025-08-17T12:35:05Z",
                "heart_rate": 82,
                "activity_level": 2,
                "location": {"type": "Point", "coordinates": [-74.007, 40.7129]}
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            export_telemetry.write_csv(test_data, temp_path)
            
            # Read back and verify
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]["collar_id"] == "SN-123"
            assert float(rows[0]["longitude"]) == -74.006
            assert float(rows[0]["latitude"]) == 40.7128
            
        finally:
            os.unlink(temp_path)
    
    def test_write_csv_empty_data(self):
        """Test CSV file writing with empty data."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            export_telemetry.write_csv([], temp_path)
            
            # Should create file with headers only
            with open(temp_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            assert len(rows) == 1  # Header only
            assert rows[0] == ['collar_id', 'timestamp', 'heart_rate', 'activity_level', 'longitude', 'latitude']
            
        finally:
            os.unlink(temp_path)


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="Tools not available")
class TestGenerateSamples:
    """Test the generate_samples.py functionality."""
    
    def test_parse_geo_coordinates_valid(self):
        """Test parsing valid geo coordinates."""
        lon, lat = generate_samples.parse_geo_coordinates("-74.0060,40.7128")
        assert lon == -74.0060
        assert lat == 40.7128
    
    def test_parse_geo_coordinates_with_spaces(self):
        """Test parsing geo coordinates with spaces."""
        lon, lat = generate_samples.parse_geo_coordinates("-74.0060, 40.7128")
        assert lon == -74.0060
        assert lat == 40.7128
    
    def test_parse_geo_coordinates_invalid_format(self):
        """Test parsing invalid geo coordinate formats."""
        with pytest.raises(ValueError, match="must be in 'lon,lat' format"):
            generate_samples.parse_geo_coordinates("-74.0060")
        
        with pytest.raises(ValueError, match="must be in 'lon,lat' format"):
            generate_samples.parse_geo_coordinates("-74.0060,40.7128,extra")
    
    def test_parse_geo_coordinates_out_of_bounds(self):
        """Test parsing out-of-bounds coordinates."""
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            generate_samples.parse_geo_coordinates("200.0,40.7128")
        
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            generate_samples.parse_geo_coordinates("-74.0060,100.0")
    
    def test_parse_heart_rate_range_single_value(self):
        """Test parsing single heart rate value."""
        min_hr, max_hr = generate_samples.parse_heart_rate_range("75")
        assert min_hr == 75
        assert max_hr == 75
    
    def test_parse_heart_rate_range_range(self):
        """Test parsing heart rate range."""
        min_hr, max_hr = generate_samples.parse_heart_rate_range("60-100")
        assert min_hr == 60
        assert max_hr == 100
    
    def test_parse_heart_rate_range_invalid(self):
        """Test parsing invalid heart rate ranges."""
        with pytest.raises(ValueError, match="Minimum heart rate must be between 30-300"):
            generate_samples.parse_heart_rate_range("20-100")
        
        with pytest.raises(ValueError, match="Maximum heart rate must be between 30-300"):
            generate_samples.parse_heart_rate_range("60-400")
        
        with pytest.raises(ValueError, match="cannot be greater than maximum"):
            generate_samples.parse_heart_rate_range("100-60")
    
    def test_get_activity_pattern_config(self):
        """Test activity pattern configuration retrieval."""
        resting_config = generate_samples.get_activity_pattern_config('resting')
        assert 'activity_weights' in resting_config
        assert 'hr_base' in resting_config
        assert 'movement_radius' in resting_config
        
        # Resting should heavily favor activity level 0
        assert resting_config['activity_weights'][0] > 0.8
    
    def test_get_activity_pattern_config_invalid(self):
        """Test invalid activity pattern."""
        with pytest.raises(ValueError, match="Unknown activity pattern"):
            generate_samples.get_activity_pattern_config('invalid')
    
    def test_generate_telemetry_sample_structure(self):
        """Test telemetry sample structure."""
        pattern_config = generate_samples.get_activity_pattern_config('walk')
        from datetime import datetime, timezone
        
        sample = generate_samples.generate_telemetry_sample(
            collar_id="SN-123",
            timestamp=datetime.now(timezone.utc),
            pattern_config=pattern_config
        )
        
        # Verify required fields
        assert 'collar_id' in sample
        assert 'timestamp' in sample
        assert 'heart_rate' in sample
        assert 'activity_level' in sample
        assert 'location' in sample
        
        # Verify data types and ranges
        assert sample['collar_id'] == "SN-123"
        assert isinstance(sample['heart_rate'], int)
        assert 30 <= sample['heart_rate'] <= 300
        assert sample['activity_level'] in [0, 1, 2]
        assert sample['location']['type'] == 'Point'
        assert len(sample['location']['coordinates']) == 2
    
    def test_generate_sample_data_deterministic(self):
        """Test deterministic sample generation with seed."""
        # Generate same data twice with same seed
        samples1 = generate_samples.generate_sample_data(
            collar_id="SN-TEST",
            count=5,
            seed=42,
            activity_pattern="walk"
        )
        
        samples2 = generate_samples.generate_sample_data(
            collar_id="SN-TEST",
            count=5,
            seed=42,
            activity_pattern="walk"
        )
        
        # Should be identical except for timestamps (which use current time)
        assert len(samples1) == len(samples2) == 5
        
        for s1, s2 in zip(samples1, samples2):
            assert s1['collar_id'] == s2['collar_id']
            assert s1['heart_rate'] == s2['heart_rate']
            assert s1['activity_level'] == s2['activity_level']
            # Coordinates should be identical (deterministic)
            assert s1['location']['coordinates'] == s2['location']['coordinates']
    
    def test_generate_sample_data_different_seeds(self):
        """Test that different seeds produce different results."""
        samples1 = generate_samples.generate_sample_data(
            collar_id="SN-TEST",
            count=5,
            seed=42,
            activity_pattern="walk"
        )
        
        samples2 = generate_samples.generate_sample_data(
            collar_id="SN-TEST",
            count=5,
            seed=123,
            activity_pattern="walk"
        )
        
        # Should be different
        assert len(samples1) == len(samples2) == 5
        
        # At least some values should differ
        differences = 0
        for s1, s2 in zip(samples1, samples2):
            if (s1['heart_rate'] != s2['heart_rate'] or 
                s1['activity_level'] != s2['activity_level'] or
                s1['location']['coordinates'] != s2['location']['coordinates']):
                differences += 1
        
        assert differences > 0, "Different seeds should produce different results"
    
    def test_generate_sample_data_custom_hr_range(self):
        """Test sample generation with custom heart rate range."""
        samples = generate_samples.generate_sample_data(
            collar_id="SN-TEST",
            count=10,
            seed=42,
            activity_pattern="walk",
            hr_range=(90, 110)
        )
        
        # All heart rates should be within specified range
        for sample in samples:
            assert 90 <= sample['heart_rate'] <= 110


if __name__ == "__main__":
    pytest.main([__file__, "-v"])