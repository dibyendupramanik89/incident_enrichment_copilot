# MCP Tool Catalog

All 20 MCP tools across both servers.

---

## Alarm Management MCP Server (Port 9000)

**Base URL:** `http://localhost:9000`  
**Protocol:** HTTP JSON-RPC 2.0  
**Authentication:** None (bearer token managed internally by MCP server)  
**Underlying API:** Alarm API Simulator at `:8000` with `Authorization: Bearer {ALARM_API_TOKEN}`

---

### 1. `search_asset`

**Purpose:** Search for assets by name, type, or site.

**Input schema:**
```json
{
  "query": "string (required) — asset name or type keyword",
  "site": "string (optional) — filter by site name",
  "unit": "string (optional) — filter by unit",
  "limit": "integer (optional, default=10)"
}
```

**Output schema:**
```json
{
  "results": [{"asset_id": "string", "name": "string", "asset_type": "string",
               "site": "string", "unit": "string", "criticality": "string",
               "health_score": "number"}],
  "total": "integer"
}
```

**Underlying API:** `GET /assets/search?query=&site=&unit=&limit=`  
**Auth:** Bearer token on Alarm API call  
**Timeout:** 15s · Retry: 3 attempts  
**Error:** 401 → "Authentication failed", 404 → "Not found"

**Example invocation:**
```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_asset","arguments":{"query":"Boiler Feed Pump","site":"EastRefinery"}}}
```

**Example response:**
```json
{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"search_asset",...}]}}
```

---

### 2. `get_asset_metadata`

**Purpose:** Full asset metadata including open alarm count, maintenance dates.

**Input schema:**
```json
{"asset_id": "string (required)"}
```

**Output schema:**
```json
{
  "asset_id": "string", "name": "string", "asset_type": "string",
  "criticality": "string", "health_score": "number",
  "open_alarm_count": "integer",
  "last_maintenance": "string (ISO date)",
  "next_maintenance": "string (ISO date)"
}
```

**Underlying API:** `GET /assets/{asset_id}/metadata`

---

### 3. `get_alarms`

**Purpose:** List alarms with filtering by asset, severity, status, with pagination.

**Input schema:**
```json
{
  "asset_id": "string (optional)",
  "severity": "string (optional) — critical|high|medium|low",
  "status": "string (optional) — active|acknowledged|closed",
  "page": "integer (optional, default=1)",
  "page_size": "integer (optional, default=50)",
  "sort_by": "string (optional)",
  "sort_order": "string (optional) — asc|desc"
}
```

**Output schema:**
```json
{
  "data": [{"alarm_id": "string", "alarm_name": "string",
             "severity": "string", "status": "string",
             "asset_id": "string", "start_time": "string"}],
  "total": "integer", "page": "integer", "page_size": "integer"
}
```

**Underlying API:** `GET /alarms?asset_id=&severity=&status=&page=&page_size=`

---

### 4. `get_alarm_detail`

**Purpose:** Full detail for a single alarm including description, timestamps, tags.

**Input schema:**
```json
{"alarm_id": "string (required)"}
```

**Output schema:**
```json
{
  "alarm_id": "string", "alarm_name": "string", "description": "string",
  "asset_id": "string", "site": "string", "unit": "string",
  "severity": "string", "status": "string",
  "start_time": "string", "ack_time": "string|null", "tag": "string"
}
```

**Underlying API:** `GET /alarms/{alarm_id}`

---

### 5. `alarm_summary`

**Purpose:** Aggregated alarm statistics over a configurable time window.

**Input schema:**
```json
{
  "asset_ids": ["string"] "(optional)",
  "time_range": {"start_time": "string (ISO)", "end_time": "string (ISO)"},
  "severity": ["string"] "(optional)",
  "group_by": ["string"] "(default: [alarm_name])",
  "kpis": ["string"] "(default: [alarm_count, recurring_rate, avg_ack_delay])"
}
```

**Output schema:**
```json
{"summary": [{"alarm_name": "string", "count": "integer", "recurring_rate": "number"}]}
```

**Underlying API:** `POST /alarms/summary`

---

### 6. `alarm_trends`

**Purpose:** Daily or weekly alarm count trends.

**Input schema:**
```json
{
  "asset_ids": ["string"] "(optional)",
  "time_range": {"start_time": "string", "end_time": "string"},
  "bucket": "string (daily|weekly, default=daily)",
  "metrics": ["string"] "(default: [alarm_count])"
}
```

**Underlying API:** `POST /alarms/trends`

---

### 7. `correlate_alarms`

**Purpose:** Detect co-occurrence correlations between alarms across assets.

**Input schema:**
```json
{
  "asset_ids": ["string"] "(required)",
  "time_range": {"start_time": "string", "end_time": "string"},
  "correlation_method": "string (default: cooccurrence)",
  "lag_window_minutes": "integer (default: 15)",
  "severity_threshold": "string (default: medium)",
  "min_support": "integer (default: 1)"
}
```

**Underlying API:** `POST /alarms/correlation`

---

### 8. `flood_analysis`

**Purpose:** Detect alarm floods (high rate in rolling window) within a unit.

**Input schema:**
```json
{
  "unit": "string (required)",
  "time_range": {"start_time": "string", "end_time": "string"},
  "threshold_count": "integer (default: 10)",
  "rolling_window_minutes": "integer (default: 10)"
}
```

**Underlying API:** `POST /alarms/flood-analysis`

---

### 9. `rationalization_candidates`

**Purpose:** Identify alarms that are candidates for rationalization (noisy, redundant, chattering).

**Input schema:**
```json
{
  "asset_ids": ["string"] "(optional)",
  "time_range": {"start_time": "string", "end_time": "string"},
  "recurrence_threshold": "integer (default: 5)"
}
```

**Underlying API:** `POST /alarms/rationalization-candidates`

---

### 10. `priority_score`

**Purpose:** AI-based alarm priority scoring with drivers.

**Input schema:**
```json
{"alarm_id": "string (required)"}
```

**Output schema:**
```json
{
  "alarm_id": "string",
  "priority_score": "number (0.0–1.0)",
  "priority_label": "string (critical|high|medium|low)",
  "drivers": ["string"],
  "calculated_at": "string (ISO)"
}
```

**Underlying API:** `POST /alarms/priority-score`

**Example response (ALM-001):**
```json
{"alarm_id":"ALM-001","priority_score":0.92,"priority_label":"critical","drivers":["high_severity","recent_onset","critical_asset","no_ack"]}
```

---

### 11. `operator_recommendations`

**Purpose:** Step-by-step operator actions for an alarm with urgency levels.

**Input schema:**
```json
{
  "alarm_id": "string (required)",
  "include_related": "boolean (default: true)",
  "include_asset_context": "boolean (default: true)",
  "include_historical_pattern": "boolean (default: true)"
}
```

**Output schema:**
```json
{
  "alarm_id": "string",
  "recommended_actions": [{"step": "integer", "action": "string", "urgency": "string"}],
  "likely_causes": ["string"],
  "asset_context": {}
}
```

**Underlying API:** `POST /recommendations/operator-actions`

---

### 12. `generate_calculation`

**Purpose:** Generate KPI calculation code for a given calculation type and filters.

**Input schema:**
```json
{
  "calculation_type": "string (e.g. alarm_rate, mttr, ack_delay)",
  "filters": {"asset_ids": ["string"], "time_range": {}}
}
```

**Underlying API:** `POST /calculation-code/generate`

---

### 13. `execute_calculation`

**Purpose:** Execute a generated calculation against live data.

**Input schema:**
```json
{
  "calculation_id": "string (returned by generate_calculation)",
  "filters": {}
}
```

**Underlying API:** `POST /calculation-code/execute`

---

## Ticketing MCP Server (Port 9001)

**Base URL:** `http://localhost:9001`  
**Protocol:** HTTP JSON-RPC 2.0  
**Authentication:** None  
**Backend:** In-memory store (mock Jira-like system)

---

### 14. `search_tickets`

**Purpose:** Search historical and open tickets by asset or free-text query.

**Input schema:**
```json
{
  "asset_id": "string (optional)",
  "query": "string (optional)",
  "status": "string (optional) — open|closed|in_progress",
  "limit": "integer (optional, default=10)"
}
```

**Output schema:**
```json
{"tickets": [{"ticket_id":"string","title":"string","status":"string","priority":"string","asset_id":"string","asset_name":"string"}]}
```

---

### 15. `get_ticket_detail`

**Purpose:** Full ticket with description, resolution notes, timeline.

**Input schema:**
```json
{"ticket_id": "string (required)"}
```

---

### 16. `create_ticket_draft`

**Purpose:** Create a draft ticket. **Does NOT write to the ticket system.** Returns a draft ID for HITL confirmation.

**Input schema:**
```json
{
  "title": "string (required)",
  "description": "string (required)",
  "asset_id": "string (required)",
  "asset_name": "string (required)",
  "alarm_ids": ["string"],
  "priority": "string (critical|high|medium|low)",
  "recommended_actions": ["string"],
  "rag_sources": ["string"]
}
```

**Output schema:**
```json
{
  "draft_id": "string (DRAFT-XXXXXXXX)",
  "title": "string",
  "description": "string",
  "priority": "string",
  "status": "draft",
  "created_at": "string"
}
```

---

### 17. `confirm_create_ticket`

**Purpose:** **HITL write gate.** Converts a draft into a real ticket. This is the only tool that writes data. Must be called explicitly by the operator.

**Input schema:**
```json
{
  "draft_id": "string (required)",
  "confirmed_by": "string (operator name)"
}
```

**Output schema:**
```json
{
  "ticket_id": "string (INC-XXXXXX)",
  "title": "string",
  "status": "open",
  "priority": "string",
  "confirmed_by": "string",
  "created_at": "string"
}
```

---

### 18. `update_ticket`

**Purpose:** Update fields of an existing ticket.

**Input schema:**
```json
{
  "ticket_id": "string (required)",
  "status": "string (optional)",
  "priority": "string (optional)",
  "notes": "string (optional)"
}
```

---

### 19. `get_draft`

**Purpose:** Retrieve a draft by ID (for GUI display and editing).

**Input schema:**
```json
{"draft_id": "string (required)"}
```

---

### 20. `list_tickets`

**Purpose:** List all tickets in the ticketing system.

**Input schema:**
```json
{"status": "string (optional)", "limit": "integer (optional, default=50)"}
```
