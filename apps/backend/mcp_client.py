"""
MCP HTTP client used by the backend orchestrator.
Calls alarm and ticketing MCP servers using JSON-RPC style tool routes.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

MCP_ALARM_URL = os.getenv("MCP_ALARM_URL", "http://localhost:9000")
MCP_TICKETING_URL = os.getenv("MCP_TICKETING_URL", "http://localhost:9001")
MCP_TIMEOUT_SECONDS = float(os.getenv("MCP_TIMEOUT_SECONDS", "20"))


class DirectAlarmClient:
    """
    Backward-compatible adapter for orchestrator code.
    Despite the class name, this client routes operations through MCP servers.
    """

    ALARM_TOOLS = {
        "search_asset",
        "get_asset_metadata",
        "get_alarms",
        "get_alarm_detail",
        "alarm_summary",
        "alarm_trends",
        "correlate_alarms",
        "flood_analysis",
        "rationalization_candidates",
        "priority_score",
        "operator_recommendations",
        "generate_calculation",
        "execute_calculation",
    }

    TICKETING_TOOLS = {
        "search_tickets",
        "get_ticket_detail",
        "create_ticket_draft",
        "confirm_create_ticket",
        "update_ticket",
        "get_draft",
        "list_tickets",
    }

    def __init__(self):
        self.trace_log: List[dict] = []

    def _server_url(self, tool_name: str) -> str:
        if tool_name in self.ALARM_TOOLS:
            return MCP_ALARM_URL
        if tool_name in self.TICKETING_TOOLS:
            return MCP_TICKETING_URL
        raise ValueError(f"Unknown MCP tool: {tool_name}")

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        server_url = self._server_url(tool_name)
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=MCP_TIMEOUT_SECONDS) as client:
                response = await client.post(f"{server_url}/tools/call", json=payload)
            duration_ms = round((time.time() - start) * 1000, 1)

            if response.status_code != 200:
                err = f"HTTP {response.status_code}: {response.text[:200]}"
                self.trace_log.append(
                    {
                        "tool": tool_name,
                        "server": server_url,
                        "duration_ms": duration_ms,
                        "success": False,
                        "error": err,
                    }
                )
                raise ValueError(err)

            body = response.json()
            content = body.get("result", {}).get("content", [])
            parsed: Dict[str, Any] = {}
            if content and content[0].get("type") == "text":
                parsed = json.loads(content[0].get("text", "{}"))
            else:
                parsed = body

            if isinstance(parsed, dict) and parsed.get("error"):
                self.trace_log.append(
                    {
                        "tool": tool_name,
                        "server": server_url,
                        "duration_ms": duration_ms,
                        "success": False,
                        "error": parsed.get("error"),
                    }
                )
                raise ValueError(parsed.get("error"))

            self.trace_log.append(
                {
                    "tool": tool_name,
                    "server": server_url,
                    "duration_ms": duration_ms,
                    "success": True,
                    "error": None,
                }
            )
            return parsed if isinstance(parsed, dict) else {"data": parsed}

        except Exception as exc:
            duration_ms = round((time.time() - start) * 1000, 1)
            self.trace_log.append(
                {
                    "tool": tool_name,
                    "server": server_url,
                    "duration_ms": duration_ms,
                    "success": False,
                    "error": str(exc),
                }
            )
            logger.warning("MCP call failed for %s: %s", tool_name, exc)
            raise

    async def search_asset(self, query: str, site: str = None, unit: str = None, limit: int = 10) -> dict:
        payload = {"query": query, "limit": limit}
        if site:
            payload["site"] = site
        if unit:
            payload["unit"] = unit
        return await self._call_tool("search_asset", payload)

    async def get_asset_metadata(self, asset_id: str, trace_id: str = None) -> dict:
        payload = {"asset_id": asset_id}
        if trace_id:
            payload["trace_id"] = trace_id
        return await self._call_tool("get_asset_metadata", payload)

    async def get_alarms(
        self,
        asset_id: str = None,
        site: str = None,
        status: str = None,
        severity: str = None,
        page: int = 1,
        trace_id: str = None,
    ) -> dict:
        payload: Dict[str, Any] = {"page": page, "page_size": 50, "sort_by": "start_time", "sort_order": "desc"}
        if asset_id:
            payload["asset_id"] = asset_id
        if site:
            payload["site"] = site
        if status:
            payload["status"] = status
        if severity:
            payload["severity"] = severity
        if trace_id:
            payload["trace_id"] = trace_id
        return await self._call_tool("get_alarms", payload)

    async def get_alarm_detail(self, alarm_id: str, trace_id: str = None) -> dict:
        payload = {"alarm_id": alarm_id}
        if trace_id:
            payload["trace_id"] = trace_id
        return await self._call_tool("get_alarm_detail", payload)

    async def alarm_summary(self, asset_ids: List[str], start_time: str, end_time: str, severity: List[str] = None, trace_id: str = None) -> dict:
        payload: Dict[str, Any] = {
            "asset_ids": asset_ids,
            "start_time": start_time,
            "end_time": end_time,
            "severity": severity or ["high", "critical"],
        }
        if trace_id:
            payload["trace_id"] = trace_id
        return await self._call_tool("alarm_summary", payload)

    async def priority_score(self, alarm_id: str, trace_id: str = None) -> dict:
        payload = {"alarm_id": alarm_id}
        if trace_id:
            payload["trace_id"] = trace_id
        return await self._call_tool("priority_score", payload)

    async def operator_recommendations(self, alarm_id: str, trace_id: str = None) -> dict:
        payload = {"alarm_id": alarm_id, "include_related": True, "include_asset_context": True}
        if trace_id:
            payload["trace_id"] = trace_id
        return await self._call_tool("operator_recommendations", payload)

    async def correlate_alarms(self, asset_ids: List[str], start_time: str, end_time: str, trace_id: str = None) -> dict:
        payload: Dict[str, Any] = {
            "asset_ids": asset_ids,
            "start_time": start_time,
            "end_time": end_time,
        }
        if trace_id:
            payload["trace_id"] = trace_id
        return await self._call_tool("correlate_alarms", payload)

    async def search_tickets(self, **kwargs: Any) -> dict:
        return await self._call_tool("search_tickets", kwargs)

    async def create_ticket_draft(self, **kwargs: Any) -> dict:
        return await self._call_tool("create_ticket_draft", kwargs)

    async def confirm_create_ticket(self, draft_id: str, confirmed_by: str = "operator") -> dict:
        return await self._call_tool("confirm_create_ticket", {"draft_id": draft_id, "confirmed_by": confirmed_by})

    async def get_draft(self, draft_id: str) -> dict:
        return await self._call_tool("get_draft", {"draft_id": draft_id})

    async def list_tickets(self) -> dict:
        return await self._call_tool("list_tickets", {})

    def get_trace(self) -> List[dict]:
        return self.trace_log

    def clear_trace(self) -> None:
        self.trace_log = []
