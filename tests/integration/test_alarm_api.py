"""
Integration tests for the Alarm API simulator (alarm-api/main.py).

Uses FastAPI's TestClient against the real in-process app — no network calls.
"""
import importlib.util
import os
import sys

import pytest
from fastapi.testclient import TestClient

_ALARM_API_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "alarm-api")
os.environ.setdefault("ALARM_API_TOKEN", "demo-token")


def _load_alarm_api_app():
    spec = importlib.util.spec_from_file_location(
        "alarm_api_main", os.path.join(_ALARM_API_DIR, "main.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["alarm_api_main"] = module
    spec.loader.exec_module(module)
    return module.app


@pytest.fixture(scope="module")
def client():
    app = _load_alarm_api_app()
    return TestClient(app)


AUTH = {"Authorization": "Bearer demo-token"}


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthentication:
    def test_missing_token_returns_401(self, client):
        resp = client.get("/assets/search", params={"query": "pump"})
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        resp = client.get(
            "/assets/search",
            params={"query": "pump"},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 401

    def test_valid_token_succeeds(self, client):
        resp = client.get("/assets/search", params={"query": "pump"}, headers=AUTH)
        assert resp.status_code == 200


class TestAssetsAndAlarms:
    def test_search_assets_returns_results(self, client):
        resp = client.get("/assets/search", params={"query": "Boiler Feed Pump"}, headers=AUTH)
        assert resp.status_code == 200
        body = resp.json()
        assert "results" in body
        assert body["total"] >= 1

    def test_asset_metadata_404_for_unknown_asset(self, client):
        resp = client.get("/assets/UNKNOWN-999/metadata", headers=AUTH)
        assert resp.status_code == 404

    def test_list_alarms_pagination(self, client):
        resp = client.get("/alarms", params={"page": 1, "page_size": 2}, headers=AUTH)
        assert resp.status_code == 200
        body = resp.json()
        assert "pagination" in body
        assert body["pagination"]["page"] == 1
        assert len(body["data"]) <= 2

    def test_alarm_detail_404_for_unknown_alarm(self, client):
        resp = client.get("/alarms/UNKNOWN-999", headers=AUTH)
        assert resp.status_code == 404

    def test_alarm_detail_includes_asset(self, client):
        list_resp = client.get("/alarms", headers=AUTH)
        alarms = list_resp.json()["data"]
        assert len(alarms) > 0
        alarm_id = alarms[0]["alarm_id"]
        resp = client.get(f"/alarms/{alarm_id}", headers=AUTH)
        assert resp.status_code == 200
        assert "asset" in resp.json()


class TestPriorityAndRecommendations:
    def test_priority_score_shape(self, client):
        alarms = client.get("/alarms", headers=AUTH).json()["data"]
        alarm_id = alarms[0]["alarm_id"]
        resp = client.post("/alarms/priority-score", json={"alarm_id": alarm_id}, headers=AUTH)
        assert resp.status_code == 200
        body = resp.json()
        assert "priority_score" in body or "priority_label" in body

    def test_operator_recommendations_shape(self, client):
        alarms = client.get("/alarms", headers=AUTH).json()["data"]
        alarm_id = alarms[0]["alarm_id"]
        resp = client.post(
            "/recommendations/operator-actions",
            json={"alarm_id": alarm_id, "include_related": True, "include_asset_context": True},
            headers=AUTH,
        )
        assert resp.status_code == 200
