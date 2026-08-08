# Connectors

This directory documents the extension point for wiring in additional **source systems**
beyond the primary Alarm Management API.

The assignment's "optional secondary source" requirement is satisfied by the
**Ticketing MCP server** (`mcp-servers/ticketing/`), which is a second, independent
MCP-integrated system (historical ticket search + ticket write path).

## Adding a new connector

A connector is any component that:

1. Owns its own credentials/config (never shared with the copilot backend directly)
2. Is fronted by an MCP server exposing typed tools (`inputSchema` / output contract)
3. Is invoked exclusively through the MCP client (`apps/backend/mcp_client.py`)

To add a new source system:

1. Create `mcp-servers/<name>/server.py` following the pattern in
   `mcp-servers/alarm-management/server.py` (JSON-RPC `/tools/list` + `/tools/call`).
2. Register its base URL as an env var (e.g. `MCP_<NAME>_URL`) in `.env.example`.
3. Add its tool names to `DirectAlarmClient` (or a new client class) in
   `apps/backend/mcp_client.py` so the orchestrator can route calls to it.
4. Document the new tools in `docs/mcp-tool-catalog.md`.
