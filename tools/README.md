# Petty Tools Documentation

This directory contains command-line tools for the Petty pet monitoring system.

## Privacy Export Script (`export_telemetry.py`)

Export telemetry data with built-in privacy controls.

### Features

- **Privacy-first design**: GPS coordinates are rounded to 4 decimal places by default (~10m precision)
- **Multiple output formats**: JSONL and CSV support
- **Full precision option**: Use `--full-geo` to preserve complete GPS precision when needed
- **Date range filtering**: Export data for specific time periods
- **Input validation**: Validates collar ID format and parameters

### Usage

```bash
# Export to JSONL with privacy protection (default 4-decimal GPS precision)
./tools/export_telemetry.py \
  --collar-id SN-123 \
  --start 2025-01-01 \
  --end 2025-01-02 \
  --format jsonl \
  --out privacy_export.jsonl

# Export to CSV with full GPS precision
./tools/export_telemetry.py \
  --collar-id SN-456 \
  --start 2025-01-01T00:00:00Z \
  --end 2025-01-02T23:59:59Z \
  --format csv \
  --out full_precision_export.csv \
  --full-geo
```

### Privacy Controls

| Flag | GPS Precision | Use Case |
|------|---------------|----------|
| Default | 4 decimals (~10m) | Privacy-protected exports for analysis |
| `--full-geo` | Full precision (~1m) | High-accuracy exports for veterinary analysis |

### Output Formats

**JSONL** (JSON Lines): Each line is a complete JSON record
```json
{"collar_id":"SN-123","timestamp":"2025-08-17T12:30:05Z","heart_rate":75,"activity_level":1,"location":{"type":"Point","coordinates":[-74.006,40.7128]}}
```

**CSV**: Tabular format with flattened GPS coordinates
```csv
collar_id,timestamp,heart_rate,activity_level,longitude,latitude
SN-123,2025-08-17T12:30:05Z,75,1,-74.006,40.7128
```

## Telemetry Sample Generator (`generate_samples.py`)

Generate deterministic sample telemetry data for testing and development.

### Features

- **Deterministic generation**: Same seed produces identical results
- **Activity patterns**: Realistic behavior simulation (resting, walk, play, mixed)
- **Configurable parameters**: Heart rate ranges, GPS coordinates, sample count
- **Realistic data**: Heart rates and movement patterns match real pet behavior
- **Input validation**: Validates all parameters with helpful error messages

### Usage

```bash
# Generate walking pattern samples
./tools/generate_samples.py \
  --collar-id SN-123 \
  --count 100 \
  --seed 42 \
  --activity-pattern walk \
  --output walking_samples.json

# Generate play pattern with custom heart rate range
./tools/generate_samples.py \
  --collar-id SN-456 \
  --count 50 \
  --seed 123 \
  --activity-pattern play \
  --hr-range 90-150 \
  --start-geo "-73.935,40.730" \
  --output play_samples.json

# Generate to stdout for piping
./tools/generate_samples.py \
  --collar-id SN-789 \
  --count 10 \
  --seed 999 \
  --activity-pattern mixed | jq '.samples[0]'
```

### Activity Patterns

| Pattern | Description | Activity Level Distribution | Heart Rate | Movement |
|---------|-------------|---------------------------|------------|----------|
| `resting` | Low activity, minimal movement | 90% Level 0, 8% Level 1, 2% Level 2 | 60±10 BPM | Very small radius |
| `walk` | Moderate activity, steady movement | 20% Level 0, 70% Level 1, 10% Level 2 | 80±15 BPM | Moderate radius |
| `play` | High activity, dynamic movement | 10% Level 0, 30% Level 1, 60% Level 2 | 120±30 BPM | Large radius |
| `mixed` | Balanced mix of all activities | 40% Level 0, 40% Level 1, 20% Level 2 | 85±25 BPM | Variable radius |

### Parameters

- `--collar-id`: Must match format `XX-123` (2 letters, dash, 3-6 digits)
- `--count`: Number of samples (1-10,000 for safety)
- `--seed`: Random seed for reproducible results
- `--activity-pattern`: Behavioral pattern simulation
- `--hr-range`: Heart rate range in BPM (30-300, e.g., "60-100" or "75")
- `--start-geo`: Starting GPS coordinates as "longitude,latitude"
- `--interval`: Time between samples in minutes (default: 5)

### Output Format

```json
{
  "samples": [
    {
      "collar_id": "SN-123",
      "timestamp": "2025-08-17T08:17:12Z",
      "heart_rate": 75,
      "activity_level": 1,
      "location": {
        "type": "Point",
        "coordinates": [-74.006, 40.7128]
      }
    }
  ],
  "metadata": {
    "collar_id": "SN-123",
    "count": 1,
    "seed": 42,
    "activity_pattern": "walk",
    "hr_range": "pattern_default",
    "start_coordinates": [-74.006, 40.7128],
    "generated_at": "2025-08-17T08:17:12Z"
  }
}
```

## Data Schema

Both tools use the standard Petty telemetry data schema:

```json
{
  "collar_id": "string (XX-123 format)",
  "timestamp": "string (ISO 8601 UTC)",
  "heart_rate": "integer (30-300 BPM)",
  "activity_level": "integer (0=resting, 1=walking, 2=playing)",
  "location": {
    "type": "Point",
    "coordinates": [longitude, latitude]
  }
}
```

## Security & Privacy

### Input Validation
- Collar IDs must match the standard format (`[A-Z]{2}-\d{3,6}`)
- Heart rates are validated within realistic ranges (30-300 BPM)
- GPS coordinates are validated within global bounds
- All text inputs are sanitized

### Privacy Protection
- GPS coordinates are rounded to 4 decimal places by default
- Export requires explicit collar ID specification
- No hidden analytics or data collection
- All privacy controls are clearly documented

### Data Quality
- Deterministic sample generation ensures reproducible tests
- Realistic heart rate ranges based on canine physiology
- Movement patterns match actual pet behavior
- Timestamp formatting follows ISO 8601 standards

## Testing

The tools include comprehensive tests covering:
- CSV and JSONL writer functionality
- Deterministic sampling with seeds
- Privacy controls and GPS precision
- Input validation and error handling
- Edge cases and boundary conditions

Run tests:
```bash
python -m pytest tests/test_tools.py -v
```

## Examples

### Privacy Audit Workflow
```bash
# 1. Generate test data
./tools/generate_samples.py --collar-id SN-123 --count 1000 --seed 42 --activity-pattern mixed --output test_data.json

# 2. Export with privacy protection (default)
./tools/export_telemetry.py --collar-id SN-123 --start 2025-01-01 --end 2025-01-02 --format csv --out privacy_protected.csv

# 3. Export with full precision for comparison
./tools/export_telemetry.py --collar-id SN-123 --start 2025-01-01 --end 2025-01-02 --format csv --out full_precision.csv --full-geo

# 4. Analyze privacy impact
diff privacy_protected.csv full_precision.csv
```

### Behavior Analysis Workflow
```bash
# Generate samples for each behavior pattern
for pattern in resting walk play mixed; do
    ./tools/generate_samples.py \
        --collar-id SN-${pattern^^} \
        --count 200 \
        --seed 42 \
        --activity-pattern $pattern \
        --output ${pattern}_behavior.json
done

# Export for analysis tools
./tools/export_telemetry.py --collar-id SN-WALK --start 2025-01-01 --end 2025-01-02 --format csv --out walk_analysis.csv
```

## Notes

- The export tool currently uses sample data; in production it would connect to the actual data store
- GPS precision balances privacy protection with analytical utility
- Activity patterns are based on real canine behavior research
- All tools follow the existing codebase patterns and security controls