"""FastAPI service exposing health and minimal endpoints for Cloud Run.

This lightweight layer reuses existing observability utilities.
"""

from fastapi import FastAPI
from typing import Dict, Any
from datetime import datetime, timezone

try:
    from common.observability.powertools import health_checker, obs_manager
except Exception:  # pragma: no cover
    health_checker = None
    obs_manager = None

app = FastAPI(title="Petty API", version="0.1.0")

@app.get("/health", tags=["system"])
async def health() -> Dict[str, Any]:
    base = {
        "service": "petty-api",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if health_checker:
        base.update(health_checker.get_health_status())
    return base

@app.get("/ready", tags=["system"])
async def ready() -> Dict[str, Any]:
    return {"ready": True, "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/version", tags=["system"])
async def version() -> Dict[str, Any]:
    return {"version": "0.1.0"}

@app.get("/observability", tags=["system"])
async def observability_flag() -> Dict[str, Any]:
    try:
        from common.observability.powertools import POWertools_AVAILABLE  # local import to avoid startup penalty
        return {"powertools": bool(POWertools_AVAILABLE)}
    except Exception:
        return {"powertools": False}
