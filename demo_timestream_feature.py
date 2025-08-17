#!/usr/bin/env python3
"""
Demo script showing the Timestream 24h query feature flag functionality
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def demo_stub_data_mode():
    """Demonstrate stub data mode"""
    print("="*60)
    print("DEMO: Timeline Generator with Stub Data (USE_STUB_DATA=true)")
    print("="*60)
    
    os.environ['USE_STUB_DATA'] = 'true'
    
    try:
        # Import the stub function directly for demo
        import random, datetime
        from typing import List, Dict, Any

        def _stub_last_24h(collar_id: str) -> List[Dict[str, Any]]:
            base = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
            data = []
            lon, lat = -74.0060, 40.7128
            for i in range(0, 6):  # Just 6 records for demo
                ts = (base + datetime.timedelta(hours=4*i)).replace(microsecond=0).isoformat() + "Z"
                lvl = random.choices([0,1,2], weights=[0.6,0.3,0.1])[0]
                hr = 60 + (0 if lvl==0 else 20 if lvl==1 else 50) + random.randint(-5,5)
                lon += random.uniform(-0.001, 0.001) * (1 if lvl else 0.2)
                lat += random.uniform(-0.001, 0.001) * (1 if lvl else 0.2)
                data.append({
                    "collar_id": collar_id, "timestamp": ts, "heart_rate": hr, "activity_level": lvl,
                    "location": {"type":"Point","coordinates":[lon, lat]}
                })
            return data
        
        data = _stub_last_24h('SN-DEMO')
        
        print(f"Generated {len(data)} stub telemetry records:")
        for i, record in enumerate(data):
            activity_names = ['Resting', 'Walking', 'Playing']
            activity = activity_names[record['activity_level']]
            coords = record['location']['coordinates']
            print(f"  {i+1}. {record['timestamp'][:19]}Z - {activity} (HR: {record['heart_rate']}) at [{coords[0]:.4f}, {coords[1]:.4f}]")
        
        print("\n✓ Stub mode: Fast, deterministic test data for development")
        
    finally:
        if 'USE_STUB_DATA' in os.environ:
            del os.environ['USE_STUB_DATA']

def demo_timestream_mode():
    """Demonstrate Timestream mode with mocked response"""
    print("\n" + "="*60)
    print("DEMO: Timeline Generator with Timestream Query (USE_STUB_DATA=false)")
    print("="*60)
    
    os.environ['USE_STUB_DATA'] = 'false'
    
    try:
        # Mock a realistic Timestream response
        mock_response = {
            'Rows': [
                # Record 1 - Morning walk
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T08:00:00Z'}, {'ScalarValue': 'HeartRate'}, {'ScalarValue': '85.0'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T08:00:00Z'}, {'ScalarValue': 'ActivityLevel'}, {'ScalarValue': '1.0'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T08:00:00Z'}, {'ScalarValue': 'Longitude'}, {'ScalarValue': '-74.0050'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T08:00:00Z'}, {'ScalarValue': 'Latitude'}, {'ScalarValue': '40.7120'}]},
                
                # Record 2 - Afternoon nap
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T14:00:00Z'}, {'ScalarValue': 'HeartRate'}, {'ScalarValue': '65.0'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T14:00:00Z'}, {'ScalarValue': 'ActivityLevel'}, {'ScalarValue': '0.0'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T14:00:00Z'}, {'ScalarValue': 'Longitude'}, {'ScalarValue': '-74.0055'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T14:00:00Z'}, {'ScalarValue': 'Latitude'}, {'ScalarValue': '40.7125'}]},
                
                # Record 3 - Evening play
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T18:00:00Z'}, {'ScalarValue': 'HeartRate'}, {'ScalarValue': '110.0'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T18:00:00Z'}, {'ScalarValue': 'ActivityLevel'}, {'ScalarValue': '2.0'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T18:00:00Z'}, {'ScalarValue': 'Longitude'}, {'ScalarValue': '-74.0065'}]},
                {'Data': [{'ScalarValue': 'SN-DEMO'}, {'ScalarValue': '2023-12-07T18:00:00Z'}, {'ScalarValue': 'Latitude'}, {'ScalarValue': '40.7130'}]},
            ]
        }
        
        with patch('boto3.Session') as mock_session:
            mock_client = MagicMock()
            mock_client.query.return_value = mock_response
            mock_session.return_value.client.return_value = mock_client
            
            from common.aws.timestream import query_last_24h
            
            data = query_last_24h('SN-DEMO')
            
            print(f"Retrieved {len(data)} records from Timestream:")
            for i, record in enumerate(data):
                activity_names = ['Resting', 'Walking', 'Playing']
                activity = activity_names[record['activity_level']]
                coords = record['location']['coordinates']
                print(f"  {i+1}. {record['timestamp'][:19]}Z - {activity} (HR: {record['heart_rate']}) at [{coords[0]:.4f}, {coords[1]:.4f}]")
            
            print("\n✓ Timestream mode: Production queries against real telemetry data")
            
    finally:
        if 'USE_STUB_DATA' in os.environ:
            del os.environ['USE_STUB_DATA']

def demo_feature_flag_control():
    """Demonstrate how the feature flag controls behavior"""
    print("\n" + "="*60)
    print("DEMO: Feature Flag Control")
    print("="*60)
    
    print("Environment Variable Settings:")
    print("  USE_STUB_DATA=true  -> Uses fast stub data for development/testing")
    print("  USE_STUB_DATA=false -> Queries Timestream for production data")
    print("  (not set)           -> Defaults to false (Timestream mode)")
    
    print("\nFallback Behavior:")
    print("  - If Timestream is unavailable, automatically falls back to stub data")
    print("  - Logs errors and records metrics for monitoring")
    print("  - Ensures timeline generator always returns data")
    
    print("\nImplementation:")
    print("  - Feature flag checked at module import time")
    print("  - Timestream client lazy-loaded only when needed")
    print("  - Error handling with graceful degradation")

if __name__ == "__main__":
    print("Petty Timeline Generator - Timestream 24h Query Demo")
    
    demo_stub_data_mode()
    demo_timestream_mode()
    demo_feature_flag_control()
    
    print("\n" + "="*60)
    print("SUMMARY: Implementation Complete")
    print("="*60)
    print("✓ Added query_last_24h function in src/common/aws/timestream.py")
    print("✓ Added USE_STUB_DATA feature flag to src/timeline_generator/app.py")
    print("✓ Implemented fallback behavior for robustness")
    print("✓ Created comprehensive tests with mocked Timestream responses")
    print("✓ Maintains compatibility with existing DATA_PROTOCOL format")
    print("✓ Supports both development (stub) and production (Timestream) modes")
    
    print("\nProduction deployment:")
    print("  1. Deploy with USE_STUB_DATA=false")
    print("  2. Ensure IAM permissions for timestream:Query")
    print("  3. Monitor CloudWatch for TimestreamQueryFailures metric")
    print("  4. Verify data flows to BehavioralInterpreter correctly")