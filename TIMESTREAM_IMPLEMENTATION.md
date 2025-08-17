# Timestream 24h Query Implementation

This implementation adds production Timestream querying to the timeline generator, replacing stub data with real telemetry queries.

## Features Added

### 1. Timestream Query Module (`src/common/aws/timestream.py`)
- `query_last_24h(collar_id)` function that queries Timestream for the last 24 hours of data
- Parameterized queries for security (collar_id filtering)
- Results ordered by time ASC as required
- Transforms Timestream multi-measure format to canonical DATA_PROTOCOL format
- Proper error handling with detailed logging

### 2. Feature Flag Support (`src/timeline_generator/app.py`)
- `USE_STUB_DATA` environment variable controls data source
- `USE_STUB_DATA=true` → uses fast stub data (development/testing)
- `USE_STUB_DATA=false` → queries Timestream (production)
- Automatic fallback to stub data if Timestream fails
- Metrics recorded for monitoring query failures

### 3. Data Format Compatibility
Maintains exact compatibility with existing DATA_PROTOCOL:
```python
{
    "collar_id": str,
    "timestamp": str,  # ISO format with Z suffix
    "heart_rate": int,
    "activity_level": int,  # 0=resting, 1=walking, 2=playing
    "location": {
        "type": "Point",
        "coordinates": [longitude, latitude]
    }
}
```

## Usage

### Development Mode (Default)
```bash
export USE_STUB_DATA=true
# Timeline generator uses fast stub data
```

### Production Mode
```bash
export USE_STUB_DATA=false
# Timeline generator queries Timestream
# Requires IAM permissions: timestream:Query
```

### Environment Variables
- `USE_STUB_DATA`: "true" or "false" (default: "false")
- `TIMESTREAM_DATABASE`: Database name (default: "PettyDB")
- `TIMESTREAM_TABLE`: Table name (default: "CollarMetrics")
- `AWS_REGION`: AWS region (default: "us-east-1")

## Testing

### Run Unit Tests
```bash
cd /path/to/Petty
python tests/test_timestream_standalone.py
```

### Run Integration Tests
```bash
python tests/test_timeline_integration.py
```

### Run Demo
```bash
PYTHONPATH=src python demo_timestream_feature.py
```

## Monitoring

The implementation adds these CloudWatch metrics:
- `TimestreamQueryFailures`: Count of failed Timestream queries
- `Requests`: Count of timeline requests (existing)

## IAM Permissions Required

For production deployment, the Lambda execution role needs:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "timestream:Query"
            ],
            "Resource": [
                "arn:aws:timestream:*:*:database/PettyDB",
                "arn:aws:timestream:*:*:database/PettyDB/table/CollarMetrics"
            ]
        }
    ]
}
```

## Implementation Details

### Query Structure
The Timestream query handles the multi-measure format:
```sql
SELECT 
    CollarId,
    time,
    measure_name,
    measure_value::double
FROM "PettyDB"."CollarMetrics"
WHERE CollarId = 'SN-123' 
    AND time >= ago(24h)
ORDER BY time ASC
```

### Error Handling
- Timestream connection failures → automatic fallback to stub data
- Invalid responses → logged with request context
- Missing data → empty result set returned
- All errors recorded in CloudWatch metrics

### Performance
- Lazy loading of Timestream client (only when needed)
- Efficient row grouping by timestamp
- Minimal data transformation overhead
- Connection pooling with retry configuration

## Files Modified/Added

### New Files
- `src/common/aws/__init__.py` - AWS utilities package
- `src/common/aws/timestream.py` - Timestream query implementation
- `tests/test_timestream_standalone.py` - Unit tests
- `tests/test_timeline_integration.py` - Integration tests
- `demo_timestream_feature.py` - Demonstration script

### Modified Files  
- `src/timeline_generator/app.py` - Added feature flag and Timestream integration

## Future Enhancements

Potential improvements for future iterations:
1. Query caching for high-traffic scenarios
2. Batch querying for multiple collar IDs
3. Configurable time window (not just 24h)
4. Query optimization based on data volume
5. Real-time streaming data integration