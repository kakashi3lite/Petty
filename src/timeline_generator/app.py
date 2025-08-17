import json, os, logging, random, datetime
from typing import List, Dict, Any
from behavioral_interpreter.interpreter import BehavioralInterpreter

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _stub_last_24h(collar_id: str) -> List[Dict[str, Any]]:
    # Simulated 24h of points every 10 minutes
    base = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    data = []
    lon, lat = -74.0060, 40.7128
    for i in range(0, 24*6):
        ts = (base + datetime.timedelta(minutes=10*i)).replace(microsecond=0).isoformat() + "Z"
        lvl = random.choices([0,1,2], weights=[0.6,0.3,0.1])[0]
        hr = 60 + (0 if lvl==0 else 20 if lvl==1 else 50) + random.randint(-5,5)
        lon += random.uniform(-0.0003, 0.0003) * (1 if lvl else 0.2)
        lat += random.uniform(-0.0003, 0.0003) * (1 if lvl else 0.2)
        data.append({
            "collar_id": collar_id, "timestamp": ts, "heart_rate": hr, "activity_level": lvl,
            "location": {"type":"Point","coordinates":[lon, lat]}
        })
    return data

def lambda_handler(event, context):
    try:
        qs = event.get("queryStringParameters") or {}
        collar_id = qs.get("collar_id") or "SN-123"
        # TODO: replace stub with Timestream query
        series = _stub_last_24h(collar_id)
        timeline = BehavioralInterpreter().analyze_timeline(series)
        return {"statusCode": 200, "body": json.dumps({"collar_id": collar_id, "timeline": timeline})}
    except Exception as e:
        logger.exception("timeline error")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
