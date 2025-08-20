import json, os, logging, random, datetime
from typing import List, Dict, Any
from behavioral_interpreter.interpreter import BehavioralInterpreter

# Import timestream query helper
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from common.aws.timestream import query_last_24h
    TIMESTREAM_AVAILABLE = True
except ImportError:
    TIMESTREAM_AVAILABLE = False

# >>> PETTY:COPILOT:BEGIN:OBS-LOGGING
# Use powertools logger/tracer/metrics; read POWERTOOLS_SERVICE_NAME + POWERTOOLS_LOG_LEVEL
# Replace print() with logger.info/exception; add metrics.add_metric('Requests', 'Count', 1)
# Decorate handlers with @tracer.capture_lambda_handler
try:
    from aws_lambda_powertools import Logger, Tracer, Metrics
    from aws_lambda_powertools.utilities.typing import LambdaContext
    AWS_POWERTOOLS_AVAILABLE = True
    logger = Logger(service=os.getenv("POWERTOOLS_SERVICE_NAME", "timeline-generator"))
    tracer = Tracer(service=os.getenv("POWERTOOLS_SERVICE_NAME", "timeline-generator"))
    metrics = Metrics(service=os.getenv("POWERTOOLS_SERVICE_NAME", "timeline-generator"), namespace="Petty")
except ImportError:
    AWS_POWERTOOLS_AVAILABLE = False
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
# <<< PETTY:COPILOT:END:OBS-LOGGING

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

@tracer.capture_lambda_handler if AWS_POWERTOOLS_AVAILABLE else lambda x: x
@logger.inject_lambda_context(log_event=True) if AWS_POWERTOOLS_AVAILABLE else lambda x: x
def lambda_handler(event, context):
    # Add metrics for request count
    if AWS_POWERTOOLS_AVAILABLE:
        metrics.add_metric(name="Requests", unit="Count", value=1)
    
    try:
        qs = event.get("queryStringParameters") or {}
        collar_id = qs.get("collar_id") or "SN-123"
        
        # >>> PETTY:COPILOT:BEGIN:TS-QUERY
        # If USE_STUB_DATA=true -> keep stub; else query last 24h asc and map to DATA_PROTOCOL dict shape
        # Feed BehavioralInterpreter() and return timeline JSON
        use_stub = os.getenv("USE_STUB_DATA", "true").lower() == "true"
        
        if use_stub or not TIMESTREAM_AVAILABLE:
            # Keep stub data for development/testing
            series = _stub_last_24h(collar_id)
        else:
            # Query last 24h from Timestream in ascending order
            series = query_last_24h(collar_id)
        # <<< PETTY:COPILOT:END:TS-QUERY
        
        timeline = BehavioralInterpreter().analyze_timeline(series)
        return {"statusCode": 200, "body": json.dumps({"collar_id": collar_id, "timeline": timeline})}
    except Exception as e:
        logger.exception("timeline error")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
