#!/usr/bin/env python3
import argparse, time, json, random, sys
try:
    import requests
except Exception:
    requests = None

def generate_payload(collar_id, lon=-74.0060, lat=40.7128):
    lvl = random.choices([0,1,2], weights=[0.6,0.3,0.1])[0]
    hr = 60 + (0 if lvl==0 else 20 if lvl==1 else 50) + random.randint(-5,5)
    payload = {
        "collar_id": collar_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "heart_rate": hr,
        "activity_level": lvl,
        "location": {"type":"Point","coordinates":[lon, lat]},
    }
    return payload

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collar-id","-c", required=True)
    ap.add_argument("--interval","-i", type=float, default=10.0)
    ap.add_argument("--endpoint-url","-e", default=None, dest="endpoint_url")
    args = ap.parse_args()

    while True:
        payload = generate_payload(args.collar_id)
        if args.endpoint_url:
            if not requests:
                print("Install requests to use --endpoint-url", file=sys.stderr); return 2
            try:
                r = requests.post(args.endpoint_url, json=payload, timeout=5)
                print(f"POST {r.status_code}: {payload}")
            except Exception as ex:
                print(f"ERR: {ex}", file=sys.stderr)
        else:
            print(json.dumps(payload))
        time.sleep(args.interval)

if __name__ == "__main__":
    sys.exit(main())
