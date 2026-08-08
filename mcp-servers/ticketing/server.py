"""
Ticketing MCP server exposed over HTTP JSON-RPC style endpoints.
"""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ticketing-mcp")

app = FastAPI(title="ticketing-mcp", version="1.0.0")


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: Dict[str, Any] = {}


TICKET_STORE: Dict[str, Dict[str, Any]] = {}
DRAFT_STORE: Dict[str, Dict[str, Any]] = {}

HISTORICAL_TICKETS = [
    {
        "ticket_id": "INC-1001",
        "title": "BFP-101 recurring low suction pressure — root cause investigation",
        "asset_id": "ASSET-001",
        "alarm_ids": ["ALM-001"],
        "status": "closed",
        "priority": "high",
        "created_at": "2026-04-10T10:30:00Z",
        "resolved_at": "2026-04-11T14:00:00Z",
        "resolution": "Replaced suction filter. Adjusted setpoint from 2.0 bar to 2.5 bar.",
        "description": "BFP-101 tripped due to sustained low suction pressure.",
    },
    {
        "ticket_id": "INC-1002",
        "title": "C-201 high discharge temperature — urgent",
        "asset_id": "ASSET-003",
        "alarm_ids": ["ALM-003"],
        "status": "in_progress",
        "priority": "critical",
        "created_at": "2026-06-14T14:20:00Z",
        "resolved_at": None,
        "resolution": None,
        "description": "Compressor C-201 discharge temperature rising.",
    },
]


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


def _all_tickets() -> list[dict]:
    return HISTORICAL_TICKETS + list(TICKET_STORE.values())


def _tools() -> list[dict]:
    return [
        {
            "name": "search_tickets",
            "description": "Search historical tickets by keyword, asset_id, or alarm_id.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "asset_id": {"type": "string"},
                    "alarm_id": {"type": "string"},
                    "status": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
            },
        },
        {
            "name": "get_ticket_detail",
            "description": "Get full detail for a specific ticket by ticket_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"ticket_id": {"type": "string"}},
                "required": ["ticket_id"],
            },
        },
        {
            "name": "create_ticket_draft",
            "description": "Create a DRAFT incident ticket preview.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "asset_id": {"type": "string"},
                    "asset_name": {"type": "string"},
                    "alarm_ids": {"type": "array", "items": {"type": "string"}},
                    "priority": {"type": "string"},
                    "recommended_actions": {"type": "array", "items": {"type": "string"}},
                    "rag_sources": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "description", "priority"],
            },
        },
        {
            "name": "confirm_create_ticket",
            "description": "Write operation. Create ticket from approved draft.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "draft_id": {"type": "string"},
                    "confirmed_by": {"type": "string"},
                },
                "required": ["draft_id", "confirmed_by"],
            },
        },
        {
            "name": "update_ticket",
            "description": "Update status, priority, or notes on an existing ticket.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "status": {"type": "string"},
                    "priority": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["ticket_id"],
            },
        },
        {
            "name": "get_draft",
            "description": "Get draft details by draft_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"draft_id": {"type": "string"}},
                "required": ["draft_id"],
            },
        },
        {
            "name": "list_tickets",
            "description": "List historical and newly created tickets.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def _dispatch(name: str, arguments: Dict[str, Any]) -> dict:
    if name == "search_tickets":
        query = (arguments.get("query") or "").lower()
        asset_id = arguments.get("asset_id")
        alarm_id = arguments.get("alarm_id")
        status = arguments.get("status")
        limit = arguments.get("limit", 5)

        results = []
        for ticket in _all_tickets():
            match = False
            if query and (
                query in ticket["title"].lower()
                or query in ticket["description"].lower()
                or query in (ticket.get("resolution") or "").lower()
            ):
                match = True
            if asset_id and ticket.get("asset_id") == asset_id:
                match = True
            if alarm_id and alarm_id in ticket.get("alarm_ids", []):
                match = True
            if not query and not asset_id and not alarm_id:
                match = True
            if status and ticket.get("status") != status:
                match = False
            if match:
                results.append(ticket)

        return {"tickets": results[:limit], "total": len(results)}

    if name == "get_ticket_detail":
        ticket_id = arguments.get("ticket_id")
        if not ticket_id:
            raise ValueError("ticket_id is required")

        all_tickets = {t["ticket_id"]: t for t in _all_tickets()}
        ticket = all_tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket '{ticket_id}' not found")
        return ticket

    if name == "create_ticket_draft":
        draft_id = "DRAFT-" + str(uuid.uuid4())[:8].upper()
        draft = {
            "draft_id": draft_id,
            "title": arguments.get("title"),
            "description": arguments.get("description"),
            "asset_id": arguments.get("asset_id"),
            "asset_name": arguments.get("asset_name"),
            "alarm_ids": arguments.get("alarm_ids", []),
            "priority": arguments.get("priority", "medium"),
            "recommended_actions": arguments.get("recommended_actions", []),
            "rag_sources": arguments.get("rag_sources", []),
            "status": "draft",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "note": "This is a DRAFT. Use confirm_create_ticket after explicit human approval.",
        }
        DRAFT_STORE[draft_id] = draft
        return draft

    if name == "confirm_create_ticket":
        draft_id = arguments.get("draft_id")
        confirmed_by = arguments.get("confirmed_by", "operator")
        if not draft_id:
            raise ValueError("draft_id is required")

        draft = DRAFT_STORE.get(draft_id)
        if not draft:
            raise ValueError(f"Draft '{draft_id}' not found or already confirmed")

        ticket_id = "INC-" + str(len(_all_tickets()) + 1001)
        ticket = {
            **draft,
            "ticket_id": ticket_id,
            "status": "open",
            "confirmed_by": confirmed_by,
            "confirmed_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
        ticket.pop("draft_id", None)
        ticket.pop("note", None)
        TICKET_STORE[ticket_id] = ticket
        del DRAFT_STORE[draft_id]

        return {
            "ticket_id": ticket_id,
            "status": "open",
            "message": f"Ticket {ticket_id} successfully created",
            "confirmed_by": confirmed_by,
            "ticket": ticket,
        }

    if name == "update_ticket":
        ticket_id = arguments.get("ticket_id")
        if not ticket_id:
            raise ValueError("ticket_id is required")

        existing = {t["ticket_id"]: t for t in _all_tickets()}.get(ticket_id)
        if not existing:
            raise ValueError(f"Ticket '{ticket_id}' not found")

        if "status" in arguments:
            existing["status"] = arguments["status"]
        if "priority" in arguments:
            existing["priority"] = arguments["priority"]
        if "note" in arguments:
            existing.setdefault("notes", []).append(
                {
                    "text": arguments["note"],
                    "added_at": datetime.datetime.utcnow().isoformat() + "Z",
                }
            )

        if ticket_id in TICKET_STORE:
            TICKET_STORE[ticket_id] = existing
        return {"ticket_id": ticket_id, "updated": existing}

    if name == "get_draft":
        draft_id = arguments.get("draft_id")
        if not draft_id:
            raise ValueError("draft_id is required")
        draft = DRAFT_STORE.get(draft_id)
        if not draft:
            raise ValueError(f"Draft '{draft_id}' not found")
        return {"draft": draft}

    if name == "list_tickets":
        return {"tickets": _all_tickets(), "total": len(_all_tickets())}

    raise ValueError(f"Unknown tool: {name}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ticketing-mcp"}


@app.post("/tools/list")
def tools_list(req: JsonRpcRequest) -> dict:
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
def tools_call(req: JsonRpcRequest) -> dict:
    if req.method != "tools/call":
        return _rpc_err(req.id, f"Unsupported method: {req.method}")
    try:
        name = req.params.get("name")
        arguments = req.params.get("arguments") or {}
        if not name:
            return _rpc_err(req.id, "Tool name is required")
        data = _dispatch(name, arguments)
        return _rpc_ok(req.id, data)
    except Exception as exc:
        logger.exception("Tool invocation failed")
        return _rpc_err(req.id, str(exc))
