"""
Unit tests for DirectAlarmClient (apps/backend/mcp_client.py).

Focus: tool→server routing, payload construction, and trace-log recording.
Network calls are monkeypatched — no live MCP servers required.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend"))

import pytest  # noqa: E402
from mcp_client import DirectAlarmClient, MCP_ALARM_URL, MCP_TICKETING_URL  # noqa: E402


class TestToolRouting:
    def setup_method(self):
        self.client = DirectAlarmClient()

    def test_alarm_tool_routes_to_alarm_server(self):
        assert self.client._server_url("get_alarms") == MCP_ALARM_URL
        assert self.client._server_url("priority_score") == MCP_ALARM_URL
        assert self.client._server_url("search_asset") == MCP_ALARM_URL

    def test_ticketing_tool_routes_to_ticketing_server(self):
        assert self.client._server_url("search_tickets") == MCP_TICKETING_URL
        assert self.client._server_url("create_ticket_draft") == MCP_TICKETING_URL

    def test_unknown_tool_raises(self):
        with pytest.raises(ValueError, match="Unknown MCP tool"):
            self.client._server_url("nonexistent_tool")


class TestPayloadConstruction:
    @pytest.mark.asyncio
    async def test_search_asset_payload(self, monkeypatch):
        client = DirectAlarmClient()
        captured = {}

        async def fake_call_tool(tool_name, arguments):
            captured["tool_name"] = tool_name
            captured["arguments"] = arguments
            return {"results": []}

        monkeypatch.setattr(client, "_call_tool", fake_call_tool)
        await client.search_asset(query="pump", site="EastRefinery", limit=5)

        assert captured["tool_name"] == "search_asset"
        assert captured["arguments"]["query"] == "pump"
        assert captured["arguments"]["site"] == "EastRefinery"
        assert captured["arguments"]["limit"] == 5

    @pytest.mark.asyncio
    async def test_get_alarms_payload_defaults(self, monkeypatch):
        client = DirectAlarmClient()
        captured = {}

        async def fake_call_tool(tool_name, arguments):
            captured["arguments"] = arguments
            return {"data": []}

        monkeypatch.setattr(client, "_call_tool", fake_call_tool)
        await client.get_alarms(asset_id="ASSET-001")

        assert captured["arguments"]["asset_id"] == "ASSET-001"
        assert captured["arguments"]["page"] == 1
        assert captured["arguments"]["sort_order"] == "desc"

    @pytest.mark.asyncio
    async def test_create_draft_payload(self, monkeypatch):
        client = DirectAlarmClient()
        captured = {}

        async def fake_call_tool(tool_name, arguments):
            captured["tool_name"] = tool_name
            captured["arguments"] = arguments
            return {"draft_id": "DRAFT-1"}

        monkeypatch.setattr(client, "_call_tool", fake_call_tool)
        await client.create_ticket_draft(
            title="Test", description="desc", asset_id="ASSET-001",
            asset_name="BFP-101", alarm_ids=["ALM-001"], priority="high",
            recommended_actions=["step1"], rag_sources=["doc.md"],
        )
        assert captured["tool_name"] == "create_ticket_draft"
        assert captured["arguments"]["priority"] == "high"


class TestTraceLog:
    @pytest.mark.asyncio
    async def test_successful_call_appends_trace(self, monkeypatch):
        client = DirectAlarmClient()

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"result": {"content": [{"type": "text", "text": '{"ok": true}'}]}}

        class FakeAsyncClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def post(self, *a, **kw):
                return FakeResponse()

        import mcp_client as mcp_client_module
        monkeypatch.setattr(mcp_client_module.httpx, "AsyncClient", FakeAsyncClient)

        result = await client._call_tool("get_alarms", {"asset_id": "ASSET-001"})
        assert result == {"ok": True}
        assert len(client.trace_log) == 1
        assert client.trace_log[0]["success"] is True
        assert client.trace_log[0]["tool"] == "get_alarms"

    def test_clear_trace(self):
        client = DirectAlarmClient()
        client.trace_log.append({"tool": "x"})
        client.clear_trace()
        assert client.trace_log == []
