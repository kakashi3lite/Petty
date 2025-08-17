"""
Tests for telemetry sample generator

Tests validate deterministic generation, schema compliance, and range validation.
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path


class TestGenerateSamples:
    """Test class for telemetry sample generator"""
    
    def __init__(self):
        self.script_path = Path(__file__).parent.parent / "tools" / "generate_samples.py"
    
    def _run_script(self, args: list, expect_success: bool = True) -> tuple[int, str, str]:
        """Run the generate_samples.py script with given arguments"""
        cmd = [sys.executable, str(self.script_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if expect_success and result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            assert False, f"Expected success but got return code {result.returncode}"
        
        return result.returncode, result.stdout, result.stderr
    
    def test_basic_functionality(self):
        """Test basic sample generation"""
        print("Testing basic functionality...")
        
        returncode, stdout, stderr = self._run_script([
            "--collar-id", "SN-TEST-001",
            "--count", "3",
            "--seed", "42"
        ])
        
        # Parse output
        samples = json.loads(stdout)
        assert len(samples) == 3, f"Expected 3 samples, got {len(samples)}"
        
        # Verify schema for first sample
        sample = samples[0]
        required_keys = {"collar_id", "timestamp", "heart_rate", "activity_level", "location"}
        assert set(sample.keys()) == required_keys, f"Missing or extra keys: {set(sample.keys())}"
        
        # Verify collar_id
        assert sample["collar_id"] == "SN-TEST-001"
        
        # Verify location structure
        location = sample["location"]
        assert location["type"] == "Point"
        assert isinstance(location["coordinates"], list)
        assert len(location["coordinates"]) == 2
        assert isinstance(location["coordinates"][0], float)  # longitude
        assert isinstance(location["coordinates"][1], float)  # latitude
        
        print("✓ Basic functionality test passed")
    
    def test_deterministic_generation(self):
        """Test that same seed produces same output"""
        print("Testing deterministic generation...")
        
        # Generate samples twice with same seed
        args = ["--collar-id", "SN-DETERMINISTIC", "--count", "5", "--seed", "123"]
        
        _, stdout1, _ = self._run_script(args)
        _, stdout2, _ = self._run_script(args)
        
        samples1 = json.loads(stdout1)
        samples2 = json.loads(stdout2)
        
        assert samples1 == samples2, "Same seed should produce identical output"
        
        print("✓ Deterministic generation test passed")
    
    def test_activity_patterns(self):
        """Test different activity patterns"""
        print("Testing activity patterns...")
        
        patterns = ["resting", "walk", "play", "mixed"]
        
        for pattern in patterns:
            _, stdout, _ = self._run_script([
                "--collar-id", f"SN-{pattern.upper()}",
                "--count", "10",
                "--seed", "42",
                "--activity-pattern", pattern
            ])
            
            samples = json.loads(stdout)
            activity_levels = [s["activity_level"] for s in samples]
            
            if pattern == "resting":
                assert all(level == 0 for level in activity_levels), f"Resting pattern should only have level 0"
            elif pattern == "walk":
                assert all(level == 1 for level in activity_levels), f"Walk pattern should only have level 1"
            elif pattern == "play":
                assert all(level == 2 for level in activity_levels), f"Play pattern should only have level 2"
            elif pattern == "mixed":
                unique_levels = set(activity_levels)
                assert len(unique_levels) > 1, f"Mixed pattern should have multiple activity levels"
                assert all(level in [0, 1, 2] for level in activity_levels), f"Invalid activity levels in mixed pattern"
        
        print("✓ Activity patterns test passed")
    
    def test_heart_rate_ranges(self):
        """Test heart rate range functionality"""
        print("Testing heart rate ranges...")
        
        # Test specific ranges with different activity patterns
        test_cases = [
            ("resting", "60-90", 0),
            ("walk", "80-120", 1),
            ("play", "100-160", 2)
        ]
        
        for pattern, hr_range, expected_activity in test_cases:
            _, stdout, _ = self._run_script([
                "--collar-id", "SN-HR-TEST",
                "--count", "10",
                "--seed", "42",
                "--activity-pattern", pattern,
                "--hr-range", hr_range
            ])
            
            samples = json.loads(stdout)
            hr_min, hr_max = map(int, hr_range.split('-'))
            
            for sample in samples:
                hr = sample["heart_rate"]
                assert hr_min <= hr <= hr_max, f"Heart rate {hr} outside range {hr_range}"
                assert sample["activity_level"] == expected_activity
        
        print("✓ Heart rate ranges test passed")
    
    def test_gps_coordinates(self):
        """Test GPS coordinate generation and random walk"""
        print("Testing GPS coordinates...")
        
        start_coords = "73.9857,40.7484"  # Times Square (without negative sign for this test)
        
        _, stdout, _ = self._run_script([
            "--collar-id", "SN-GPS-TEST",
            "--count", "10",
            "--seed", "42",
            "--start-geo", start_coords
        ])
        
        samples = json.loads(stdout)
        
        # Check first sample starts at specified coordinates
        first_location = samples[0]["location"]["coordinates"]
        expected_lon, expected_lat = 73.9857, 40.7484
        assert abs(first_location[0] - expected_lon) < 0.0001, f"First longitude should be close to start"
        assert abs(first_location[1] - expected_lat) < 0.0001, f"First latitude should be close to start"
        
        # Check that coordinates change (random walk)
        all_coords = [s["location"]["coordinates"] for s in samples]
        unique_coords = set(tuple(coord) for coord in all_coords)
        assert len(unique_coords) > 1, "Coordinates should change during random walk"
        
        # Check that walk doesn't go too far (reasonable bounds)
        for coords in all_coords[1:]:  # Skip first as it's the start point
            lon_diff = abs(coords[0] - expected_lon)
            lat_diff = abs(coords[1] - expected_lat)
            assert lon_diff < 0.01, f"Longitude deviation too large: {lon_diff}"
            assert lat_diff < 0.01, f"Latitude deviation too large: {lat_diff}"
        
        print("✓ GPS coordinates test passed")
    
    def test_negative_coordinates(self):
        """Test negative GPS coordinates (like NYC)"""
        print("Testing negative GPS coordinates...")
        
        # Test negative coordinates by using equals sign format
        returncode, stdout, stderr = self._run_script([
            "--collar-id", "SN-NEG-GPS",
            "--count", "3",
            "--seed", "42",
            "--start-geo=-74.0060,40.7128"  # NYC coordinates with equals
        ])
        
        samples = json.loads(stdout)
        first_location = samples[0]["location"]["coordinates"]
        
        # Should start with negative longitude
        assert first_location[0] < 0, "Should have negative longitude for NYC"
        assert first_location[1] > 0, "Should have positive latitude for NYC"
        
        print("✓ Negative GPS coordinates test passed")
    
    def test_file_output(self):
        """Test output to file"""
        print("Testing file output...")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            returncode, stdout, stderr = self._run_script([
                "--collar-id", "SN-FILE-TEST",
                "--count", "3",
                "--seed", "42",
                "--output", output_file
            ])
            
            # Check that stdout is empty and stderr has confirmation
            assert stdout.strip() == "", "Should not output to stdout when using --output"
            assert "Generated 3 samples" in stderr, "Should show confirmation message"
            
            # Check file contents
            with open(output_file, 'r') as f:
                file_contents = f.read()
            
            samples = json.loads(file_contents)
            assert len(samples) == 3, "File should contain 3 samples"
            
        finally:
            os.unlink(output_file)
        
        print("✓ File output test passed")
    
    def test_schema_validation(self):
        """Test that output matches DATA_PROTOCOL.md schema"""
        print("Testing schema validation...")
        
        _, stdout, _ = self._run_script([
            "--collar-id", "SN-SCHEMA-TEST",
            "--count", "5",
            "--seed", "42"
        ])
        
        samples = json.loads(stdout)
        
        for i, sample in enumerate(samples):
            # Required fields
            assert "collar_id" in sample, f"Sample {i}: missing collar_id"
            assert "timestamp" in sample, f"Sample {i}: missing timestamp"
            assert "heart_rate" in sample, f"Sample {i}: missing heart_rate"
            assert "activity_level" in sample, f"Sample {i}: missing activity_level"
            assert "location" in sample, f"Sample {i}: missing location"
            
            # Field types and formats
            assert isinstance(sample["collar_id"], str), f"Sample {i}: collar_id should be string"
            assert isinstance(sample["timestamp"], str), f"Sample {i}: timestamp should be string"
            assert isinstance(sample["heart_rate"], int), f"Sample {i}: heart_rate should be int"
            assert isinstance(sample["activity_level"], int), f"Sample {i}: activity_level should be int"
            
            # Timestamp format (ISO 8601)
            timestamp = sample["timestamp"]
            assert timestamp.endswith("Z"), f"Sample {i}: timestamp should end with Z"
            assert "T" in timestamp, f"Sample {i}: timestamp should contain T"
            
            # Activity level range
            activity = sample["activity_level"]
            assert activity in [0, 1, 2], f"Sample {i}: activity_level {activity} not in [0,1,2]"
            
            # Heart rate range (reasonable bounds)
            hr = sample["heart_rate"]
            assert 30 <= hr <= 200, f"Sample {i}: heart_rate {hr} outside reasonable range"
            
            # Location structure
            location = sample["location"]
            assert location["type"] == "Point", f"Sample {i}: location type should be 'Point'"
            assert "coordinates" in location, f"Sample {i}: location missing coordinates"
            coords = location["coordinates"]
            assert len(coords) == 2, f"Sample {i}: coordinates should have 2 elements"
            assert isinstance(coords[0], float), f"Sample {i}: longitude should be float"
            assert isinstance(coords[1], float), f"Sample {i}: latitude should be float"
            
            # GPS coordinate bounds (reasonable world coordinates)
            lon, lat = coords
            assert -180 <= lon <= 180, f"Sample {i}: longitude {lon} outside valid range"
            assert -90 <= lat <= 90, f"Sample {i}: latitude {lat} outside valid range"
        
        print("✓ Schema validation test passed")
    
    def test_error_handling(self):
        """Test error conditions"""
        print("Testing error handling...")
        
        error_cases = [
            # Missing required argument
            (["--count", "5"], "should require collar-id"),
            # Invalid heart rate range
            (["--collar-id", "SN-ERR", "--hr-range", "invalid"], "should reject invalid hr-range"),
            # Invalid GPS coordinates
            (["--collar-id", "SN-ERR", "--start-geo", "invalid"], "should reject invalid coordinates"),
            # Invalid count
            (["--collar-id", "SN-ERR", "--count", "0"], "should reject zero count"),
            # Invalid activity pattern
            (["--collar-id", "SN-ERR", "--activity-pattern", "invalid"], "should reject invalid pattern"),
        ]
        
        for args, description in error_cases:
            returncode, stdout, stderr = self._run_script(args, expect_success=False)
            assert returncode != 0, f"Error case failed: {description}"
        
        print("✓ Error handling test passed")


def main():
    """Run all tests"""
    test_runner = TestGenerateSamples()
    
    print("=" * 60)
    print("Telemetry Sample Generator Tests")
    print("=" * 60)
    
    # List of test methods
    test_methods = [
        test_runner.test_basic_functionality,
        test_runner.test_deterministic_generation,
        test_runner.test_activity_patterns,
        test_runner.test_heart_rate_ranges,
        test_runner.test_gps_coordinates,
        test_runner.test_negative_coordinates,
        test_runner.test_file_output,
        test_runner.test_schema_validation,
        test_runner.test_error_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_method()
            passed += 1
        except Exception as e:
            print(f"❌ {test_method.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())