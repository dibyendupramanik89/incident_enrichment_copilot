# Architecture — Incident & Ticket Enrichment Copilot

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     OPERATOR  (Browser)                         │
│                   Gradio UI  :7860                              │
│   [Tab: Investigation] [Alarm & Asset] [Ticket Draft]           │
│   [Similar Tickets] [RAG Citations] [MCP Trace] [Audit Log]     │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP REST (requests library)
                      │ POST /chat · POST /confirm-ticket
┌─────────────────────▼───────────────────────────────────────────┐
│                  BACKEND API  :8080                             │
│  FastAPI app (apps/backend/api.py)                              │
│  Routes: /health  /chat  /confirm-ticket  /drafts/{id}          │
│          /tickets                                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               INPUT GUARDRAILS (guardrails.py)           │  │
│  │  • PII detection: email, phone, IP, account, credential  │  │
│  │  • PII masking before forwarding to orchestrator         │  │
│  │  • Prompt injection: 9 regex patterns                    │  │
│  │  • Policy enforcement (exploit/hack/inject blocked)      │  │
│  │  • Length validation (max 2000 chars, min 3 chars)       │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │ clean_message                      │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │         COPILOT ORCHESTRATOR (orch.py)                   │  │
│  │         9-step pipeline                                  │  │
│  │                                                          │  │
│  │  Step 1  Intent detection                                │  │
│  │          keyword classifier → create_incident /          │  │
│  │          investigate / summarize_alarm /                 │  │
│  │          get_recommendations / find_similar /            │  │
│  │          correlate / general_inquiry                     │  │
│  │                                                          │  │
│  │  Step 2  Asset resolution via MCP                        │  │
│  │          extract asset name from message → search_asset  │  │
│  │                                                          │  │
│  │  Step 3  Alarm retrieval + detail via MCP                │  │
│  │          get_alarms(asset_id) → pick highest severity    │  │
│  │          get_alarm_detail(alarm_id)                      │  │
│  │                                                          │  │
│  │  Step 4  Priority scoring via MCP                        │  │
│  │          priority_score(alarm_id) → 0.0–1.0 + label      │  │
│  │                                                          │  │
│  │  Step 5  Operator recommendations via MCP                │  │
│  │          operator_recommendations(alarm_id)              │  │
│  │                                                          │  │
│  │  Step 6  Similar ticket search via MCP                   │  │
│  │          search_tickets(asset_id, query)                 │  │
│  │                                                          │  │
│  │  Step 7  BM25 RAG retrieval (local)                      │  │
│  │          retrieve(query, k=4) from rag/.index/           │  │
│  │                                                          │  │
│  │  Step 8  LLM synthesis                                   │  │
│  │          OpenAI GPT-4o-mini with full context            │  │
│  │          Fallback: structured text from MCP data         │  │
│  │                                                          │  │
│  │  Step 9  Draft ticket creation via MCP                   │  │
│  │          create_ticket_draft(...) → DRAFT-XXXXXXXX       │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │ raw_answer                         │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              OUTPUT GUARDRAILS (guardrails.py)           │  │
│  │  • PII redaction in generated answer                     │  │
│  │  • Confidence scoring (RAG score + alarm data + length)  │  │
│  │  • Low-confidence caveat appended if score < 0.40        │  │
│  │  • Uncertainty phrase detection                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │ HTTP JSON-RPC POST /tools/call
          │                             │ HTTP JSON-RPC POST /tools/call
┌─────────▼──────────────┐   ┌─────────▼────────────────────────┐
│  ALARM MANAGEMENT MCP  │   │     TICKETING MCP  :9001          │
│  mcp-servers/alarm-    │   │     mcp-servers/ticketing/        │
│  management/server.py  │   │     server.py                     │
│                        │   │                                   │
│  Port: 9000            │   │  Port: 9001                       │
│  13 tools              │   │  7 tools                          │
│  FastAPI app           │   │  FastAPI app                      │
│  httpx async client    │   │  In-memory TICKET_STORE           │
│  Retry (3 attempts)    │   │  In-memory DRAFT_STORE            │
│  Timeout (15s)         │   │  Historical tickets seeded        │
│  Bearer auth header    │   │                                   │
│  Trace header          │   │  HITL gate: confirm_create_ticket │
└─────────┬──────────────┘   └───────────────────────────────────┘
          │ Bearer Authorization: demo-token
          │ x-metadata-tag: mcp-tool
          │ trace_id: {uuid}
┌─────────▼──────────────────────────────────────────────────────┐
│               ALARM API SIMULATOR  :8000                        │
│               alarm-api/main.py                                 │
│                                                                 │
│  14 endpoints (FastAPI):                                        │
│  GET  /health                                                   │
│  GET  /assets/search?query=&site=&unit=&limit=                  │
│  GET  /assets/{asset_id}/metadata                               │
│  GET  /alarms?asset_id=&severity=&status=&page=&page_size=      │
│  GET  /alarms/{alarm_id}                                        │
│  POST /alarms/summary                                           │
│  POST /alarms/trends                                            │
│  POST /alarms/correlation                                       │
│  POST /alarms/flood-analysis                                    │
│  POST /alarms/rationalization-candidates                        │
│  POST /alarms/priority-score                                    │
│  POST /recommendations/operator-actions                         │
│  POST /calculation-code/generate                                │
│  POST /calculation-code/execute                                 │
│                                                                 │
│  In-memory data: 7 assets, 7 alarms, recommendations           │
│  Auth: Bearer token validation on all non-health endpoints      │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   RAG PIPELINE                                  │
│                                                                 │
│  rag/documents/  (6 markdown files)                             │
│       │                                                         │
│  rag/ingestion/ingest.py                                        │
│       │  Reads all .md/.txt files                               │
│       │  Chunks at 900 chars with 150-char overlap              │
│       │  Computes per-term IDF across all chunks                │
│       │  Saves to rag/.index/index.json                         │
│       │  → 60 chunks total                                      │
│                                                                 │
│  rag/retrieval/retriever.py (RAGRetriever)                      │
│       │  Loads index from rag/.index/index.json                 │
│       │  retrieve(query, k=4):                                  │
│       │    tokenise(query) → BM25 score each chunk              │
│       │    sort by score → normalise → filter MIN_SCORE=0.10    │
│       │    return [{source, content, score, chunk_id}]          │
│                                                                 │
│  apps/backend/retriever.py                                      │
│       Adapter: tries to import from rag/retrieval/              │
│       Falls back to inline BM25 if path not available           │
└────────────────────────────────────────────────────────────────┘
```

---

## Complete Request Flow Narrative

### Step-by-step: "Prepare an incident for the highest-priority active alarm in EastRefinery"

**1. User Input**
Operator types the query in the Gradio chat box and clicks "Run Investigation".

**2. HTTP Call**
Frontend makes `POST http://localhost:8080/chat` with body `{"message": "..."}`.

**3. Input Guardrails**
`InputGuardrails.run(message)` checks:
- Not too short, not too long (truncates at 2000 chars)
- No PII patterns (email, phone, IP, credentials) — masks if found
- No prompt injection phrases (9 regex patterns)
- No policy violations (SQL injection attempts, hacking keywords)
Returns `GuardrailResult(passed=True, text=cleaned_message, warnings=[])`.

**4. Intent Detection**
`detect_intent("prepare an incident...")` matches `"prepare an incident"` keyword → returns `"create_incident"`.

**5. Asset Resolution via MCP**
Message contains `"EastRefinery"` → site filter applied. No explicit asset name → defaults to "Boiler Feed Pump" search.
MCP Client sends `POST http://localhost:9000/tools/call` with body:
```json
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"search_asset","arguments":{"query":"Boiler Feed Pump","site":"EastRefinery"}}}
```
Alarm MCP calls `GET http://localhost:8000/assets/search?query=Boiler+Feed+Pump&site=EastRefinery&limit=10` with `Authorization: Bearer demo-token`.
Returns ASSET-001 (BFP-101, criticality=critical).

**6. Alarm Retrieval + Detail**
MCP `get_alarms(asset_id=ASSET-001)` → Alarm API `GET /alarms?asset_id=ASSET-001` → 1 alarm: ALM-001 (critical, active).
MCP `get_alarm_detail(ALM-001)` → full alarm context.

**7. Priority Score**
MCP `priority_score(ALM-001)` → Alarm API `POST /alarms/priority-score` → score=0.92, label="critical", drivers=["high_severity","recent_onset","critical_asset"].

**8. Operator Recommendations**
MCP `operator_recommendations(ALM-001)` → Alarm API `POST /recommendations/operator-actions` → 3 step-by-step actions.

**9. Similar Tickets**
MCP Client → Ticketing MCP → `search_tickets(asset_id=ASSET-001, query="...")` → INC-1001 matched.

**10. BM25 RAG Retrieval**
`RAGRetriever.retrieve("Boiler Feed Pump 101 Pump prepare an incident Low Suction Pressure", k=4)`:
- Tokenises query
- BM25 scores all 60 chunks
- Top 4 returned: `incident_enrichment_overview.md` (1.00), `historical_resolutions.md` (0.91), `troubleshooting_guide.md` (0.74), `alarm_response_playbook.md` (0.68)

**11. LLM Synthesis (or Fallback)**
If `OPENAI_API_KEY` set: sends structured prompt to GPT-4o-mini with all context (asset, alarm, priority, recommendations, RAG chunks, similar tickets). Temperature=0.2 for factual answers.
If no key: `_fallback_answer()` generates structured markdown from the raw data.

**12. Output Guardrails**
`OutputGuardrails.run(answer, rag_docs, alarm_data)`:
- Redacts any PII in answer
- Scores confidence (RAG scores + alarm data + word count) → 0.71
- No caveat needed (above 0.40 threshold)
Returns cleaned answer with confidence score.

**13. Draft Ticket Creation**
Because intent=`create_incident`, orchestrator calls Ticketing MCP `create_ticket_draft(...)` → DRAFT-113B3271 created in memory.

**14. Response Assembly**
Backend returns JSON with: `answer`, `intent`, `asset`, `alarm`, `priority`, `recommendations`, `rag_citations[4]`, `similar_tickets[1]`, `mcp_trace[7]`, `guardrail_warnings[]`, `draft`.

**15. GUI Population**
Frontend receives response and populates all 7 tabs simultaneously. Operator reviews the ticket draft, optionally edits title/description/priority, then clicks "Confirm Ticket" to trigger the HITL write.

**16. HITL Confirmation**
`POST /confirm-ticket` with `draft_id=DRAFT-113B3271` → Ticketing MCP `confirm_create_ticket` → ticket INC-XXXXXX created in store.

---

## Authentication Boundaries

| Boundary | Method | Secret |
|---|---|---|
| Operator → Backend | None (local dev) | — |
| Backend → Alarm MCP | None (internal) | — |
| Alarm MCP → Alarm API | `Authorization: Bearer {token}` | `ALARM_API_TOKEN` env var |
| Backend → Ticketing MCP | None (internal) | — |
| Backend → OpenAI | SDK `api_key=` | `OPENAI_API_KEY` env var |

Secrets never appear in logs or responses.

---

## Observability

- Structured logging via Python `logging` module (INFO level)
- Every MCP tool call logged: tool name, server, duration_ms, success/error
- MCP trace returned in every `/chat` response
- Guardrail warnings returned in every response
- Gradio Audit Log tab shows session history
