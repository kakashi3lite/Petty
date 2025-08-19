"""
Basic tests for DSAR functionality
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_export_tool():
    """Test the export telemetry tool"""
    tools_path = Path(__file__).parent.parent / "tools"
    sys.path.insert(0, str(tools_path))

    from export_telemetry import DSARExporter

    # Test basic export functionality
    exporter = DSARExporter()

    # Test user data export
    export_data = exporter.export_user_telemetry(
        user_id="test-user-123",
        start_date="2024-01-01T00:00:00Z",
        end_date="2024-01-31T23:59:59Z",
        apply_dp=True
    )

    assert export_data['user_ids'] == ["test-user-123"]
    assert 'request_id' in export_data
    assert 'data' in export_data
    assert export_data['total_records'] > 0

    # Test manifest creation
    manifest = exporter.create_export_manifest(export_data, export_data['request_id'])

    assert manifest['manifest_version'] == "1.0"
    assert manifest['export_type'] == "dsar_telemetry"
    assert 'data_integrity' in manifest
    assert 'checksum' in manifest['data_integrity']
    assert 'signature' in manifest['data_integrity']

    # Test signed bundle creation
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        bundle_path = exporter.create_signed_bundle(export_data, tmp_file.name)
        assert Path(bundle_path).exists()
        assert Path(bundle_path).stat().st_size > 0

        # Clean up
        Path(bundle_path).unlink()

    print("✓ Export tool tests passed")


def test_dsar_processor():
    """Test DSAR processor validation"""
    # Mock AWS region to avoid client initialization
    import os
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    from dsar_processor.app import DSARRequestValidator

    # Test valid request
    valid_request = {
        'user_id': 'test-user-123',
        'request_type': 'export',
        'data_types': ['behavioral_events', 'sensor_metrics'],
        'date_range': {
            'start': '2024-01-01T00:00:00Z',
            'end': '2024-01-31T23:59:59Z'
        }
    }

    validated = DSARRequestValidator.validate_request(valid_request)
    assert validated['user_id'] == 'test-user-123'
    assert validated['request_type'] == 'export'
    assert 'request_id' in validated
    assert 'created_at' in validated

    # Test invalid request
    invalid_request = {
        'user_id': 'ab',  # Too short
        'request_type': 'invalid',  # Invalid type
    }

    try:
        DSARRequestValidator.validate_request(invalid_request)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "validation failed" in str(e)

    print("✓ DSAR processor tests passed")


def test_dsar_delete():
    """Test DSAR delete functionality"""
    # Mock AWS region to avoid client initialization
    import os
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    from dsar_delete.app import DSARDataDeleter

    deleter = DSARDataDeleter("test-db", "test-table")

    # Test soft deletion
    result = deleter.delete_user_data(
        user_id="test-user-123",
        data_types=["behavioral_events"],
        deletion_type="soft",
        retention_policy="standard"
    )

    assert result['user_id'] == "test-user-123"
    assert result['deletion_type'] == "soft"
    assert result['retention_policy'] == "standard"
    assert result['status'] == "completed"
    assert 'deletion_id' in result

    print("✓ DSAR delete tests passed")


if __name__ == "__main__":
    print("Running DSAR tests...")

    test_export_tool()
    test_dsar_processor()
    test_dsar_delete()

    print("\n✅ All DSAR tests passed successfully!")
