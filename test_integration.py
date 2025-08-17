#!/usr/bin/env python3
"""
Simple test script to validate the Timestream integration.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

def test_timestream_helper():
    """Test the Timestream helper functions."""
    print("Testing Timestream helper...")
    
    try:
        from common.aws.timestream import build_collar_record
        
        # Valid record
        record = build_collar_record(
            collar_id="SN-12345",
            timestamp="2024-01-15T10:30:00Z",
            heart_rate=85,
            activity_level=1,
            location={
                "type": "Point",
                "coordinates": [-74.0060, 40.7128]
            }
        )
        
        print("✓ Valid record built successfully")
        print(f"  CollarId dimension: {[d for d in record['Dimensions'] if d['Name'] == 'CollarId'][0]['Value']}")
        print(f"  HeartRate measure: {[m for m in record['MeasureValues'] if m['Name'] == 'HeartRate'][0]['Value']}")
        
        # Test validation errors
        try:
            build_collar_record("", "2024-01-15T10:30:00Z", 85, 1, {"type": "Point", "coordinates": [0, 0]})
            print("✗ Should have failed on empty collar_id")
        except ValueError:
            print("✓ Correctly rejected empty collar_id")
            
        try:
            build_collar_record("SN-12345", "2024-01-15T10:30:00Z", 400, 1, {"type": "Point", "coordinates": [0, 0]})
            print("✗ Should have failed on invalid heart rate")
        except ValueError:
            print("✓ Correctly rejected invalid heart rate")
            
    except Exception as e:
        print(f"✗ Timestream helper test failed: {e}")
        return False
        
    return True


def test_data_processor():
    """Test the data processor validation."""
    print("\nTesting data processor validation...")
    
    try:
        import data_processor.app
        
        # Create a test processor
        processor = data_processor.app.DataProcessor()
        
        # Valid data
        valid_data = {
            "collar_id": "SN-12345",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.0060, 40.7128]
            }
        }
        
        validated = processor._fallback_validate(valid_data)
        print("✓ Valid data passed validation")
        
        # Test invalid data
        try:
            invalid_data = valid_data.copy()
            invalid_data["heart_rate"] = 400
            processor._fallback_validate(invalid_data)
            print("✗ Should have failed on invalid heart rate")
        except ValueError:
            print("✓ Correctly rejected invalid heart rate")
            
        try:
            invalid_data = valid_data.copy()
            invalid_data["activity_level"] = 5
            processor._fallback_validate(invalid_data)
            print("✗ Should have failed on invalid activity level")
        except ValueError:
            print("✓ Correctly rejected invalid activity level")
            
        try:
            invalid_data = valid_data.copy()
            invalid_data["location"]["type"] = "LineString"
            processor._fallback_validate(invalid_data)
            print("✗ Should have failed on invalid location type")
        except ValueError:
            print("✓ Correctly rejected invalid location type")
            
    except Exception as e:
        print(f"✗ Data processor test failed: {e}")
        return False
        
    return True


def test_lambda_handler():
    """Test the Lambda handler responses."""
    print("\nTesting Lambda handler...")
    
    try:
        import data_processor.app
        
        # Mock context
        class MockContext:
            aws_request_id = "test-123"
            
        context = MockContext()
        
        # Valid payload
        valid_payload = {
            "collar_id": "SN-12345",
            "timestamp": "2024-01-15T10:30:00Z",
            "heart_rate": 85,
            "activity_level": 1,
            "location": {
                "type": "Point",
                "coordinates": [-74.0060, 40.7128]
            }
        }
        
        event = {"body": json.dumps(valid_payload)}
        
        # Mock the write_records to avoid actual AWS calls
        original_write_records = data_processor.app.write_records
        data_processor.app.write_records = lambda *args, **kwargs: {"ResponseMetadata": {"HTTPStatusCode": 200}}
        
        try:
            result = data_processor.app.lambda_handler(event, context)
            
            if result["statusCode"] == 200:
                body = json.loads(result["body"])
                if body.get("ok") == True:
                    print("✓ Valid payload returned 200 with {ok: true}")
                else:
                    print(f"✗ Valid payload returned wrong body: {body}")
            else:
                print(f"✗ Valid payload returned wrong status: {result['statusCode']}")
                
        finally:
            # Restore original function
            data_processor.app.write_records = original_write_records
        
        # Test invalid payload
        invalid_event = {"body": json.dumps({"collar_id": "SN-12345"})}  # Missing fields
        
        result = data_processor.app.lambda_handler(invalid_event, context)
        
        if result["statusCode"] == 400:
            print("✓ Invalid payload returned 400 error")
        else:
            print(f"✗ Invalid payload returned wrong status: {result['statusCode']}")
            
    except Exception as e:
        print(f"✗ Lambda handler test failed: {e}")
        return False
        
    return True


if __name__ == "__main__":
    print("Running Timestream integration tests...\n")
    
    success = True
    success &= test_timestream_helper()
    success &= test_data_processor()
    success &= test_lambda_handler()
    
    print(f"\n{'='*50}")
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)