"""
Alarm Management MCP server exposed over HTTP.
Implements a lightweight MCP-compatible JSON-RPC surface:
- POST /tools/list
- POST /tools/call
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("alarm-mcp")

app = FastAPI(title="alarm-management-mcp", version="1.0.0")

ALARM_API_BASE = os.getenv("ALARM_API_BASE_URL", "http://alarm-api:8000")
ALARM_API_TOKEN = os.getenv("ALARM_API_TOKEN", "demo-token")
TIMEOUT = float(os.getenv("MCP_TIMEOUT_SECONDS", "15"))
MAX_RETRIES = int(os.getenv("MCP_MAX_RETRIES", "3"))


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: Dict[str, Any] = {}


def _headers(trace_id: Optional[str] = None) -> dict:
    headers = {
        "Authorization": f"Bearer {ALARM_API_TOKEN}",
        "Content-Type": "application/json",
        "x-client-id": "alarm-mcp-server",
        "x-metadata-tag": "mcp-tool",
    }
    if trace_id:
        headers["trace_id"] = trace_id
    return headers


def _rpc_ok(req_id: Any, data: Any) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(data, default=str),
                }
            ]
        },
    }


def _rpc_err(req_id: Any, msg: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"error": msg}),
                }
            ]
        },
    }


async def _get(path: str, params: dict | None = None, trace_id: str | None = None) -> dict:
    url = f"{ALARM_API_BASE}{path}"
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, params=params or {}, headers=_headers(trace_id))
            if resp.status_code == 401:
                raise ValueError("Authentication failed — check ALARM_API_TOKEN")
            if resp.status_code == 404:
                raise ValueError(f"Not found: {path}")
            if resp.status_code == 422:
                raise ValueError(f"Validation error: {resp.text}")
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException:
            if attempt == MAX_RETRIES - 1:
                raise ValueError(f"Alarm API timeout after {MAX_RETRIES} attempts: {url}")
            await asyncio.sleep(1.5 ** attempt)
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"HTTP error {exc.response.status_code}: {exc.response.text[:200]}")


async def _post(path: str, body: dict, trace_id: str | None = None) -> dict:
    url = f"{ALARM_API_BASE}{path}"
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(url, json=body, headers=_headers(trace_id))
            if resp.status_code == 401:
                raise ValueError("Authentication failed")
            if resp.status_code == 404:
                raise ValueError(f"Not found: {path}")
            if resp.status_code == 422:
                raise ValueError(f"Validation error: {resp.text}")
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException:
            if attempt == MAX_RETRIES - 1:
                raise ValueError(f"Alarm API timeout after {MAX_RETRIES} attempts: {url}")
            await asyncio.sleep(1.5 ** attempt)
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"HTTP error {exc.response.status_code}: {exc.response.text[:200]}")


def _tools() -> list[dict]:
    return [
        {
            "name": "search_asset",
            "description": "Search assets by name, type, site, or unit.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "site": {"type": "string"},
                    "unit": {"type": "string"},
                    "trace_id": {"type": "string"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_asset_metadata",
            "description": "Get full metadata for an asset.",
            "inputSchema": {
                "type": "object",
                "properties": {"asset_id": {"type": "string"}, "trace_id": {"type": "string"}},
                "required": ["asset_id"],
            },
        },
        {
            "name": "get_alarms",
            "description": "List alarms with optional filters and pagination.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string"},
                    "site": {"type": "string"},
                    "unit": {"type": "string"},
                    "status": {"type": "string"},
                    "severity": {"type": "string"},
                    "page": {"type": "integer", "default": 1},
                    "page_size": {"type": "integer", "default": 50},
                    "sort_by": {"type": "string", "default": "start_time"},
                    "sort_order": {"type": "string", "default": "desc"},
                    "trace_id": {"type": "string"},
                },
            },
        },
        {
            "name": "get_alarm_detail",
            "description": "Get full detail for one alarm.",
            "inputSchema": {
                "type": "object",
                "properties": {"alarm_id": {"type": "string"}, "trace_id": {"type": "string"}},
                "required": ["alarm_id"],
            },
        },
        {
            "name": "alarm_summary",
            "description": "Aggregated alarm KPI summary.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset_ids": {"type": "array", "items": {"type": "string"}},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "severity": {"type": "array", "items": {"type": "string"}},
                    "group_by": {"type": "array", "items": {"type": "string"}},
                    "kpis": {"type": "array", "items": {"type": "string"}},
                    "trace_id": {"type": "string"},
                },
                "required": ["start_time", "end_time"],
            },
        },
        {
            "name": "alarm_trends",
            "description": "Get bucketed trend data.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset_ids": {"type": "array", "items": {"type": "string"}},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "bucket": {"type": "string", "default": "daily"},
                    "metrics": {"type": "array", "items": {"type": "string"}},
                    "trace_id": {"type": "string"},
                },
                "required": ["start_time", "end_time"],
            },
        },
        {
            "name": "correlate_alarms",
            "description": "Find co-occurring correlated alarms.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset_ids": {"type": "array", "items": {"type": "string"}},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "correlation_method": {"type": "string", "default": "cooccurrence"},
                    "lag_window_minutes": {"type": "integer", "default": 15},
                    "severity_threshold": {"type": "string", "default": "medium"},
                    "trace_id": {"type": "string"},
                },
                "required": ["asset_ids", "start_time", "end_time"],
            },
        },
        {
            "name": "flood_analysis",
            "description": "Detect alarm flood windows.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "unit": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "threshold_count": {"type": "integer", "default": 10},
                    "rolling_window_minutes": {"type": "integer", "default": 10},
                    "trace_id": {"type": "string"},
                },
                "required": ["unit", "start_time", "end_time"],
            },
        },
        {
            "name": "rationalization_candidates",
            "description": "Find nuisance alarm candidates.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset_ids": {"type": "array", "items": {"type": "string"}},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "recurrence_threshold": {"type": "integer", "default": 5},
                    "trace_id": {"type": "string"},
                },
                "required": ["start_time", "end_time"],
            },
        },
        {
            "name": "priority_score",
            "description": "Score alarm operational priority.",
            "inputSchema": {
                "type": "object",
                "properties": {"alarm_id": {"type": "string"}, "trace_id": {"type": "string"}},
                "required": ["alarm_id"],
            },
        },
        {
            "name": "operator_recommendations",
            "description": "Get step-by-step operator recommendations.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "alarm_id": {"type": "string"},
                    "include_related": {"type": "boolean", "default": True},
                    "include_asset_context": {"type": "boolean", "default": True},
                    "trace_id": {"type": "string"},
                },
                "required": ["alarm_id"],
            },
        },
        {
            "name": "generate_calculation",
            "description": "Generate KPI calculation code.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "calculation_type": {"type": "string"},
                    "unit": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "trace_id": {"type": "string"},
                },
                "required": ["calculation_type", "start_time", "end_time"],
            },
        },
        {
            "name": "execute_calculation",
            "description": "Execute generated KPI calculation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "calculation_id": {"type": "string"},
                    "unit": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "trace_id": {"type": "string"},
                },
                "required": ["calculation_id", "start_time", "end_time"],
            },
        },
    ]


async def _dispatch(name: str, arguments: Dict[str, Any]) -> dict:
    trace_id = arguments.pop("trace_id", None) or str(uuid.uuid4())

    if name == "search_asset":
        return await _get("/assets/search", params=arguments, trace_id=trace_id)

    if name == "get_asset_metadata":
        asset_id = arguments.get("asset_id")
        if not asset_id:
            raise ValueError("asset_id is required")
        return await _get(f"/assets/{asset_id}/metadata", trace_id=trace_id)

    if name == "get_alarms":
        return await _get("/alarms", params=arguments, trace_id=trace_id)

    if name == "get_alarm_detail":
        alarm_id = arguments.get("alarm_id")
        if not alarm_id:
            raise ValueError("alarm_id is required")
        return await _get(f"/alarms/{alarm_id}", trace_id=trace_id)

    if name == "alarm_summary":
        body = {
            "asset_ids": arguments.get("asset_ids"),
            "time_range": {"start_time": arguments["start_time"], "end_time": arguments["end_time"]},
            "severity": arguments.get("severity"),
            "group_by": arguments.get("group_by", ["alarm_name"]),
            "kpis": arguments.get("kpis", ["alarm_count", "recurring_rate", "avg_ack_delay"]),
        }
        return await _post("/alarms/summary", body, trace_id=trace_id)

    if name == "alarm_trends":
        body = {
            "asset_ids": arguments.get("asset_ids"),
            "time_range": {"start_time": arguments["start_time"], "end_time": arguments["end_time"]},
            "bucket": arguments.get("bucket", "daily"),
            "metrics": arguments.get("metrics", ["alarm_count"]),
        }
        return await _post("/alarms/trends", body, trace_id=trace_id)

    if name == "correlate_alarms":
        body = {
            "asset_ids": arguments["asset_ids"],
            "time_range": {"start_time": arguments["start_time"], "end_time": arguments["end_time"]},
            "correlation_method": arguments.get("correlation_method", "cooccurrence"),
            "lag_window_minutes": arguments.get("lag_window_minutes", 15),
            "severity_threshold": arguments.get("severity_threshold", "medium"),
            "min_support": 1,
        }
        return await _post("/alarms/correlation", body, trace_id=trace_id)

    if name == "flood_analysis":
        body = {
            "unit": arguments["unit"],
            "time_range": {"start_time": arguments["start_time"], "end_time": arguments["end_time"]},
            "threshold_count": arguments.get("threshold_count", 10),
            "rolling_window_minutes": arguments.get("rolling_window_minutes", 10),
        }
        return await _post("/alarms/flood-analysis", body, trace_id=trace_id)

    if name == "rationalization_candidates":
        body = {
            "asset_ids": arguments.get("asset_ids"),
            "time_range": {"start_time": arguments["start_time"], "end_time": arguments["end_time"]},
            "recurrence_threshold": arguments.get("recurrence_threshold", 5),
        }
        return await _post("/alarms/rationalization-candidates", body, trace_id=trace_id)

    if name == "priority_score":
        alarm_id = arguments.get("alarm_id")
        if not alarm_id:
            raise ValueError("alarm_id is required")
        return await _post("/alarms/priority-score", {"alarm_id": alarm_id}, trace_id=trace_id)

    if name == "operator_recommendations":
        alarm_id = arguments.get("alarm_id")
        if not alarm_id:
            raise ValueError("alarm_id is required")
        body = {
            "alarm_id": alarm_id,
            "include_related": arguments.get("include_related", True),
            "include_asset_context": arguments.get("include_asset_context", True),
            "include_historical_pattern": True,
        }
        return await _post("/recommendations/operator-actions", body, trace_id=trace_id)

    if name == "generate_calculation":
        body = {
            "calculation_type": arguments["calculation_type"],
            "filters": {
                "unit": arguments.get("unit", ""),
                "start_time": arguments["start_time"],
                "end_time": arguments["end_time"],
            },
        }
        return await _post("/calculation-code/generate", body, trace_id=trace_id)

    if name == "execute_calculation":
        body = {
            "calculation_id": arguments["calculation_id"],
            "filters": {
                "unit": arguments.get("unit", ""),
                "start_time": arguments["start_time"],
                "end_time": arguments["end_time"],
            },
        }
        return await _post("/calculation-code/execute", body, trace_id=trace_id)

    raise ValueError(f"Unknown tool: {name}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "alarm-management-mcp"}


@app.post("/tools/list")
async def tools_list(req: JsonRpcRequest) -> dict:
    if req.method != "tools/list":
        return _rpc_err(req.id, f"Unsupported method: {req.method}")
    return {
        "jsonrpc": "2.0",
        "id": req.id,
        "result": {
            "tools": _tools(),
        },
    }


@app.post("/tools/call")
async def tools_call(req: JsonRpcRequest) -> dict:
    if req.method != "tools/call":
        return _rpc_err(req.id, f"Unsupported method: {req.method}")
    try:
        name = req.params.get("name")
        arguments = req.params.get("arguments") or {}
        if not name:
            return _rpc_err(req.id, "Tool name is required")
        data = await _dispatch(name, arguments)
        return _rpc_ok(req.id, data)
    except Exception as exc:
        logger.exception("Tool invocation failed")
        return _rpc_err(req.id, str(exc))
