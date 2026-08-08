"""
Integration tests for the Ticketing MCP server (mcp-servers/ticketing/server.py).

Fully self-contained (no external API) — exercised via FastAPI TestClient
through the JSON-RPC /tools/list and /tools/call endpoints.
"""
import importlib.util
import os
import sys

import pytest
from fastapi.testclient import TestClient

_TICKETING_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-servers", "ticketing")


def _load_ticketing_app():
    spec = importlib.util.spec_from_file_location(
        "ticketing_mcp_server", os.path.join(_TICKETING_DIR, "server.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["ticketing_mcp_server"] = module
    spec.loader.exec_module(module)
    return module.app


@pytest.fixture(scope="module")
def client():
    app = _load_ticketing_app()
    return TestClient(app)


def _rpc_call(client, name, arguments):
    resp = client.post(
        "/tools/call",
        json={"jsonrpc": "2.0", "id": "1", "method": "tools/call",
              "params": {"name": name, "arguments": arguments}},
    )
    assert resp.status_code == 200
    body = resp.json()
    content = body["result"]["content"][0]["text"]
    import json
    return json.loads(content)


class TestHealthAndDiscovery:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "ticketing-mcp"

    def test_tools_list_returns_7_tools(self, client):
        resp = client.post(
            "/tools/list",
            json={"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}},
        )
        assert resp.status_code == 200
        tools = resp.json()["result"]["tools"]
        names = {t["name"] for t in tools}
        assert names == {
            "search_tickets", "get_ticket_detail", "create_ticket_draft",
            "confirm_create_ticket", "update_ticket", "get_draft", "list_tickets",
        }


class TestSearchAndDetail:
    def test_search_tickets_by_asset_id(self, client):
        result = _rpc_call(client, "search_tickets", {"asset_id": "ASSET-001"})
        assert result["total"] >= 1
        assert any(t["ticket_id"] == "INC-1001" for t in result["tickets"])

    def test_get_ticket_detail_not_found(self, client):
        result = _rpc_call(client, "get_ticket_detail", {"ticket_id": "INC-9999"})
        assert "error" in result


class TestDraftAndConfirmWorkflow:
    def test_create_draft_then_confirm(self, client):
        draft = _rpc_call(client, "create_ticket_draft", {
            "title": "Test Incident",
            "description": "Test description",
            "asset_id": "ASSET-001",
            "asset_name": "Boiler Feed Pump 101",
            "alarm_ids": ["ALM-001"],
            "priority": "high",
            "recommended_actions": ["Inspect suction strainer"],
            "rag_sources": ["troubleshooting_guide.md"],
        })
        assert draft["status"] == "draft"
        assert draft["draft_id"].startswith("DRAFT-")

        confirmed = _rpc_call(client, "confirm_create_ticket", {
            "draft_id": draft["draft_id"], "confirmed_by": "test-operator",
        })
        assert confirmed["status"] == "open"
        assert confirmed["ticket"]["confirmed_by"] == "test-operator"

    def test_confirm_unknown_draft_returns_error(self, client):
        result = _rpc_call(client, "confirm_create_ticket", {
            "draft_id": "DRAFT-DOES-NOT-EXIST", "confirmed_by": "operator",
        })
        assert "error" in result

    def test_get_draft_after_creation(self, client):
        draft = _rpc_call(client, "create_ticket_draft", {
            "title": "T", "description": "D", "priority": "medium",
        })
        fetched = _rpc_call(client, "get_draft", {"draft_id": draft["draft_id"]})
        assert fetched["draft"]["draft_id"] == draft["draft_id"]


class TestListAndUpdate:
    def test_list_tickets_includes_historical(self, client):
        result = _rpc_call(client, "list_tickets", {})
        ids = {t["ticket_id"] for t in result["tickets"]}
        assert "INC-1001" in ids

    def test_update_ticket_unknown_returns_error(self, client):
        result = _rpc_call(client, "update_ticket", {"ticket_id": "INC-9999", "status": "closed"})
        assert "error" in result
