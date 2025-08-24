"""Tests for FastAPI service skeleton.

Ensures basic system endpoints respond and shape is stable.
"""

from fastapi.testclient import TestClient

import api_service

client = TestClient(api_service.app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"
    assert "timestamp" in data


def test_ready_endpoint():
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["ready"] is True


def test_version_endpoint():
    resp = client.get("/version")
    assert resp.status_code == 200
    assert resp.json()["version"] == "0.1.0"


def test_observability_flag_endpoint():
    resp = client.get("/observability")
    assert resp.status_code == 200
    assert "powertools" in resp.json()
