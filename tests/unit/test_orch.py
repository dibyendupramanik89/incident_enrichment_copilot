"""
Unit tests for CopilotOrchestrator.detect_intent (apps/backend/orch.py).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend"))

import pytest  # noqa: E402
from orch import CopilotOrchestrator  # noqa: E402


@pytest.fixture
def orchestrator():
    return CopilotOrchestrator()


class TestIntentDetection:
    @pytest.mark.asyncio
    async def test_create_incident_intent(self, orchestrator):
        intent = await orchestrator.detect_intent("Please create a ticket for this alarm")
        assert intent == "create_incident"

    @pytest.mark.asyncio
    async def test_find_similar_intent(self, orchestrator):
        intent = await orchestrator.detect_intent("Show me similar tickets for this issue")
        assert intent == "find_similar"

    @pytest.mark.asyncio
    async def test_investigate_intent(self, orchestrator):
        intent = await orchestrator.detect_intent(
            "Investigate recurring alarms on BFP-101 over last 90 days"
        )
        assert intent == "investigate"

    @pytest.mark.asyncio
    async def test_get_recommendations_intent(self, orchestrator):
        intent = await orchestrator.detect_intent("What actions should I take for this alarm?")
        assert intent == "get_recommendations"

    @pytest.mark.asyncio
    async def test_general_inquiry_fallback(self, orchestrator):
        intent = await orchestrator.detect_intent("Hello there")
        assert intent == "general_inquiry"


class TestAssetResolution:
    @pytest.mark.asyncio
    async def test_resolves_known_asset_name(self, orchestrator, monkeypatch):
        async def fake_search_asset(query, site=None):
            return {"results": [{"asset_id": "ASSET-001", "name": "Boiler Feed Pump 101"}]}

        monkeypatch.setattr(orchestrator.alarm_client, "search_asset", fake_search_asset)
        asset = await orchestrator.resolve_asset("Investigate BFP-101 alarm", trace_id="t1")
        assert asset is not None
        assert asset["asset_id"] == "ASSET-001"

    @pytest.mark.asyncio
    async def test_returns_none_when_search_fails(self, orchestrator, monkeypatch):
        async def fake_search_asset(query, site=None):
            raise ConnectionError("MCP unreachable")

        monkeypatch.setattr(orchestrator.alarm_client, "search_asset", fake_search_asset)
        asset = await orchestrator.resolve_asset("Investigate BFP-101 alarm", trace_id="t1")
        assert asset is None
