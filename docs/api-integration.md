# API Integration

This document explains how the **Alarm Management API simulator** (`alarm-api/`) is wired
into the rest of the system, and how the copilot backend is forbidden from calling it directly.

## Overview

```
Backend Orchestrator → MCP Client → Alarm Management MCP Server → Alarm API Simulator
                                  → Ticketing MCP Server           (in-memory store)
```

The copilot backend **never** calls `alarm-api` directly. All access goes through the
Alarm Management MCP server (`mcp-servers/alarm-management/server.py`), which is the only
component holding the `ALARM_API_TOKEN` and the `ALARM_API_BASE_URL`.

## Alarm API Simulator (`alarm-api/main.py`)

A FastAPI service that simulates a real industrial Alarm Management System. It is stateless
and serves fixed in-memory seed data (7 assets, 7 alarms across 2 sites).

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness check |
| `/assets/search` | GET | Search assets by name/type/site/unit |
| `/assets/{asset_id}/metadata` | GET | Full asset metadata + open alarm count |
| `/alarms` | GET | List alarms (filter + paginate) |
| `/alarms/{alarm_id}` | GET | Alarm detail + embedded asset |
| `/alarms/summary` | POST | Aggregated KPI summary over a time range |
| `/alarms/trends` | POST | Bucketed trend series |
| `/alarms/correlation` | POST | Co-occurrence correlation across assets |
| `/alarms/flood-analysis` | POST | Alarm flood window detection |
| `/alarms/rationalization-candidates` | POST | Nuisance/redundant alarm detection |
| `/alarms/priority-score` | POST | Alarm priority score + label + drivers |
| `/recommendations/operator-actions` | POST | Step-by-step operator recommendations |
| `/calculation-code/generate` | POST | Generate KPI calculation code |
| `/calculation-code/execute` | POST | Execute a generated calculation |

### Authentication

Every endpoint (except `/health`) requires:

```
Authorization: Bearer <ALARM_API_TOKEN>
```

`_check_auth()` in `alarm-api/main.py` returns:
- `401 Missing bearer token` — header absent or not prefixed with `Bearer `
- `401 Invalid token` — token does not match `ALARM_API_TOKEN` env var (default `demo-token`)

### Error mapping

| Source condition | HTTP status | MCP server behavior |
|---|---|---|
| Unknown `asset_id` / `alarm_id` | 404 | Raised as `ValueError` and returned as `{"error": "..."}` in the JSON-RPC result |
| Invalid query params | 422 | Wrapped as `ValueError: Validation error: ...` |
| Timeout | — | MCP server retries up to `MCP_MAX_RETRIES` (default 3) with exponential backoff (`1.5^attempt` seconds), then raises `ValueError` |
| Bad token | 401 | Propagated as `ValueError("Authentication failed...")` |

## How the MCP server wraps the API

`mcp-servers/alarm-management/server.py` maps each of its **13 MCP tools** to one HTTP call
against `alarm-api`, injecting:

- `Authorization: Bearer <ALARM_API_TOKEN>`
- `x-client-id: alarm-mcp-server`
- `x-metadata-tag: mcp-tool`
- `trace_id` header for correlation (auto-generated if the caller doesn't supply one)

Example — `priority_score` tool:

```python
if name == "priority_score":
    alarm_id = arguments.get("alarm_id")
    if not alarm_id:
        raise ValueError("alarm_id is required")
    return await _post("/alarms/priority-score", {"alarm_id": alarm_id}, trace_id=trace_id)
```

See [`docs/mcp-tool-catalog.md`](mcp-tool-catalog.md) for the full tool-by-tool schema mapping.

## Starting the Alarm API standalone

```bash
ALARM_API_TOKEN=demo-token \
  .venv/bin/python -m uvicorn alarm-api.main:app --port 8000 --reload

curl -H "Authorization: Bearer demo-token" \
  "http://localhost:8000/assets/search?query=pump"
```

## Configuration

| Variable | Default | Used by |
|---|---|---|
| `ALARM_API_BASE_URL` | `http://alarm-api:8000` | Alarm MCP server |
| `ALARM_API_TOKEN` | `demo-token` | Alarm API + Alarm MCP server |
| `MCP_TIMEOUT_SECONDS` | `15` (MCP→API), `20` (backend→MCP) | Both hops |
| `MCP_MAX_RETRIES` | `3` | Alarm MCP server retry policy |

## Ticketing (no external API)

The Ticketing MCP server (`mcp-servers/ticketing/server.py`) does not call an external
API — it owns its own in-memory `TICKET_STORE` / `DRAFT_STORE`, seeded with 2 historical
tickets. This keeps the assignment self-contained while still demonstrating a full
MCP write-path (`create_ticket_draft` → HITL confirmation → `confirm_create_ticket`).
