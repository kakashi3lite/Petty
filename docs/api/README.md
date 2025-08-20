# Petty API Documentation

## Overview

The Petty API provides RESTful endpoints for pet monitoring, behavioral analysis, and real-time alerts. All endpoints require authentication and implement comprehensive rate limiting and security controls.

## Base URL

```
Production: https://api.petty.ai/v1
Staging: https://staging-api.petty.ai/v1
Development: http://localhost:3000/v1
```

## Authentication

### API Key Authentication
```http
Authorization: Bearer pk_your_api_key_here
```

### JWT Token Authentication
```http
Authorization: Bearer jwt_token_here
```

## Rate Limiting

| Endpoint Type | Rate Limit | Window |
|---------------|------------|---------|
| Data Ingestion | 100 req/min | 1 minute |
| Query APIs | 1000 req/min | 1 minute |
| Real-time APIs | 500 req/min | 1 minute |

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642694400
```

## OpenAPI Specification

### Core Endpoints

#### POST /ingest
Ingest collar sensor data for behavioral analysis.

**Request:**
```json
{
  "collar_id": "SN-12345",
  "timestamp": "2024-01-20T10:30:00Z",
  "heart_rate": 85,
  "activity_level": 0.7,
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy": 5.0
  },
  "temperature": 38.5,
  "battery_level": 0.85,
  "signal_strength": -45
}
```

**Response:**
```json
{
  "status": "success",
  "events_detected": 2,
  "request_id": "req_abc123",
  "processed_at": "2024-01-20T10:30:01Z"
}
```

**cURL Example:**
```bash
curl -X POST https://api.petty.ai/v1/ingest \
  -H "Authorization: Bearer pk_your_api_key" \
  -H "Content-Type: application/json" \
  -d @collar_data.json
```

#### GET /realtime
Get real-time pet status and recent activity.

**Parameters:**
- `collar_id` (required): Collar identifier
- `window` (optional): Time window in minutes (default: 60)

**Response:**
```json
{
  "collar_id": "SN-12345",
  "pet_info": {
    "name": "Buddy",
    "breed": "Golden Retriever",
    "age": 3
  },
  "current_status": {
    "activity": "resting",
    "heart_rate": 65,
    "location": "home",
    "last_seen": "2024-01-20T10:29:45Z"
  },
  "health_score": 0.92,
  "alerts": [],
  "last_updated": "2024-01-20T10:30:00Z"
}
```

#### GET /pet-timeline
Retrieve behavioral timeline and events.

**Parameters:**
- `collar_id` (required): Collar identifier
- `start_time` (optional): ISO 8601 timestamp
- `end_time` (optional): ISO 8601 timestamp
- `limit` (optional): Maximum events to return (default: 100)

**Response:**
```json
{
  "timeline": [
    {
      "event_id": "evt_abc123",
      "timestamp": "2024-01-20T10:15:00Z",
      "event_type": "play_session",
      "confidence": 0.89,
      "duration": 1200,
      "metadata": {
        "intensity": "high",
        "location_type": "park"
      }
    }
  ],
  "total_count": 23,
  "has_more": false
}
```

#### GET /pet-plan
Get personalized care recommendations.

**Response:**
```json
{
  "pet_id": "pet_12345",
  "care_plan": {
    "nutrition": {
      "daily_calories": 1200,
      "meal_frequency": 2,
      "treats_allowed": 3
    },
    "exercise": {
      "daily_minutes": 90,
      "intensity": "moderate",
      "activities": ["walk", "fetch", "swimming"]
    },
    "health": {
      "vet_checkup_due": "2024-03-15",
      "vaccinations_due": [],
      "weight_target": "25-27kg"
    }
  },
  "recommendations": [
    {
      "type": "exercise",
      "priority": "high",
      "message": "Increase daily exercise by 15 minutes",
      "reason": "Activity level below breed average"
    }
  ],
  "last_updated": "2024-01-20T08:00:00Z"
}
```

#### POST /submit-feedback
Submit user feedback on behavioral events.

**Request:**
```json
{
  "event_id": "evt_abc123",
  "user_feedback": "correct",
  "confidence": 0.95,
  "notes": "Dog was indeed playing with neighbor's dog"
}
```

**Response:**
```json
{
  "status": "success",
  "feedback_id": "fb_xyz789",
  "processed_at": "2024-01-20T10:30:05Z"
}
```

### WebSocket Endpoints

#### /ws/realtime
Real-time WebSocket connection for live updates.

**Connection:**
```javascript
const ws = new WebSocket('wss://api.petty.ai/ws/realtime?collar_id=SN-12345&token=jwt_token');
```

**Message Types:**
```json
// Activity Update
{
  "type": "activity_update",
  "collar_id": "SN-12345",
  "activity": "running",
  "timestamp": "2024-01-20T10:30:00Z"
}

// Alert
{
  "type": "alert",
  "collar_id": "SN-12345",
  "alert_type": "low_activity",
  "severity": "medium",
  "message": "Buddy has been inactive for 4 hours",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

## Data Models

### CollarData
```typescript
interface CollarData {
  collar_id: string;        // Pattern: ^[A-Z]{2}-\d{3,6}$
  timestamp: string;        // ISO 8601 format
  heart_rate: number;       // BPM, 40-200 range
  activity_level: number;   // 0.0-1.0 scale
  location?: {
    latitude: number;       // -90 to 90
    longitude: number;      // -180 to 180
    accuracy: number;       // Meters
  };
  temperature?: number;     // Celsius, 35-42 range
  battery_level?: number;   // 0.0-1.0 scale
  signal_strength?: number; // dBm
}
```

### BehaviorEvent
```typescript
interface BehaviorEvent {
  event_id: string;
  timestamp: string;
  event_type: 'resting' | 'walking' | 'running' | 'playing' | 'eating' | 'sleeping';
  confidence: number;       // 0.0-1.0 scale
  duration?: number;        // Seconds
  metadata?: {
    [key: string]: any;
  };
}
```

### UserFeedback
```typescript
interface UserFeedback {
  event_id: string;
  user_feedback: 'correct' | 'incorrect' | 'partially_correct';
  confidence?: number;      // 0.0-1.0 scale
  notes?: string;           // Max 500 characters
  timestamp?: string;       // Auto-generated if not provided
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid collar_id format",
    "details": {
      "field": "collar_id",
      "expected": "^[A-Z]{2}-\\d{3,6}$",
      "received": "invalid-id"
    },
    "request_id": "req_abc123",
    "timestamp": "2024-01-20T10:30:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing authentication |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Security

### Input Validation
- All inputs are validated against strict schemas
- SQL injection protection via parameterized queries
- XSS protection via output encoding
- File upload restrictions and scanning

### Rate Limiting
- Token bucket algorithm implementation
- Per-endpoint and per-user limits
- Circuit breaker protection
- Automatic scaling based on load

### Privacy Controls
- Location data redaction options
- PII masking in logs
- GDPR compliance features
- Data retention policies

## SDKs and Client Libraries

### Python SDK
```python
from petty_sdk import PettyClient

client = PettyClient(api_key="pk_your_api_key")
response = client.get_realtime_data("SN-12345")
print(response.current_status.activity)
```

### JavaScript/Node.js SDK
```javascript
import { PettyClient } from '@petty/sdk';

const client = new PettyClient({ apiKey: 'pk_your_api_key' });
const data = await client.getRealTimeData('SN-12345');
console.log(data.currentStatus.activity);
```

### Dart/Flutter SDK
```dart
import 'package:petty_sdk/petty_sdk.dart';

final client = PettyClient(apiKey: 'pk_your_api_key');
final data = await client.getRealTimeData('SN-12345');
print(data.currentStatus.activity);
```

## Testing

### Test Environment
```
Base URL: https://test-api.petty.ai/v1
Test API Key: pk_test_123456789
```

### Mock Data Generator
```bash
# Generate test collar data
curl -X POST https://test-api.petty.ai/v1/generate-test-data \
  -H "Authorization: Bearer pk_test_123456789" \
  -d '{"collar_id": "SN-TEST", "duration": "1h"}'
```

### Postman Collection
Download our [Postman collection](assets/petty-api.postman_collection.json) for easy API testing.

## Support

- **Documentation Issues**: [GitHub Issues](https://github.com/kakashi3lite/Petty/issues)
- **API Support**: [api-support@petty.ai](mailto:api-support@petty.ai)
- **Status Page**: [status.petty.ai](https://status.petty.ai)

---

**Version**: v1.0.0 | **Last Updated**: January 20, 2024