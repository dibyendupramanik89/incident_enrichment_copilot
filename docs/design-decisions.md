# Design Decisions

## 1. MCP Protocol: HTTP JSON-RPC over stdio

**Decision:** Implement MCP as HTTP JSON-RPC 2.0 (POST endpoints) rather than using stdio transport or the official MCP SDK.

**Rationale:**
- HTTP transport enables Docker Compose networking — each service runs in its own container and communicates over the Docker network
- HTTP is debuggable with `curl` and standard tooling
- stdio transport requires a single process boundary, which conflicts with containerised deployment
- Avoids a heavy SDK dependency for a well-understood protocol

**Trade-off:** Not protocol-compatible with MCP clients that expect stdio transport (e.g. Claude Desktop). Would require an HTTP→stdio adapter to interop with those clients.

---

## 2. ChromaDB + Embeddings (with BM25 fallback)

**Decision:** Use dense semantic retrieval with `nomic-embed-text` embeddings stored in a local ChromaDB collection. Keep a pure-Python BM25 fallback for environments where ChromaDB or the embedding service is unavailable.

**Rationale:**
- Semantic retrieval improves recall on short, operational documents where lexical variation is common.
- `nomic-embed-text` via Ollama or the nomic client is lightweight to run locally and works well for domain-specific short texts.
- ChromaDB offers a simple local vector store that is easy to persist in the repository for demos.
- A BM25 fallback provides a reliable, zero-dependency path for CI or constrained execution environments.

**Trade-off:** Dense retrieval requires an embedding service (Ollama or remote embedding API) and a vector store. The BM25 fallback preserves the zero-ML path for testing and quick demos.

**Scale threshold:** Consider hybrid sparse+dense ranking when corpus sizes or precision requirements increase significantly.

---

## 3. Fallback LLM Answer

**Decision:** Generate a structured text answer from raw MCP + RAG data when `OPENAI_API_KEY` is absent, rather than returning an error.

**Rationale:**
- Makes the system fully usable without an OpenAI account
- Satisfies all format requirements (markdown sections, citations, MCP trace)
- Easier to demo and evaluate locally
- Reduces evaluation risk: the assignment can be assessed without an API key

**Trade-off:** Fallback answer is templated, not synthesised. It may feel mechanical compared to an LLM-generated response.

---

## 4. In-memory Ticket Store

**Decision:** Use an in-memory dictionary for the mock ticketing system rather than a real database or Jira integration.

**Rationale:**
- Assignment specifies "candidate-built mock ticketing API" as a valid option
- Eliminates Jira/Azure DevOps credentials from the evaluation environment
- Keeps Docker Compose self-contained (no external services)
- Seeded with realistic historical tickets for demo purposes

**Trade-off:** Tickets reset on service restart. Production would use PostgreSQL or the real ticketing API.

---

## 5. Input Guardrails before Orchestration

**Decision:** Apply PII masking and injection detection *before* any data reaches the orchestrator or LLM.

**Rationale:**
- PII should never reach the LLM — it could be logged or echoed in responses
- Prompt injection via the user input field is the most common attack vector for LLM applications
- Guardrails at the boundary are more reliable than guardrails inside the prompt

**Implementation:** `InputGuardrails.run(message)` in `guardrails.py` — pure Python regex, no external library.

---

## 6. HITL as a Hard Gate, Not a Soft Suggestion

**Decision:** The `confirm_create_ticket` tool is the *only* path that writes to the ticket store. The orchestrator never calls it automatically.

**Rationale:**
- Assignment requirement: "Require explicit approval before a ticket write operation"
- Ticket creation has real operational consequences — a false ticket wastes engineer time
- The 7-tab GUI is designed so the operator can review and edit the draft before confirming

**Implementation:** `create_ticket_draft` creates a draft (no side effects). The frontend's "Confirm Ticket" button triggers a separate `POST /confirm-ticket` API call.

---

## 7. Single Orchestrator, Not Agent Loop

**Decision:** Use a fixed 9-step pipeline in `orch.py` rather than an LLM-driven agent loop (ReAct, function calling, etc.).

**Rationale:**
- Predictable: every query follows the same tool-call sequence; no non-deterministic planning
- Debuggable: all 9 steps logged; MCP trace always contains the same call types
- Sufficient for the defined use cases (the query types are known and bounded)
- Avoids agent hallucination in tool selection

**Trade-off:** Not flexible for queries outside the defined intent space. An LLM agent loop would handle open-ended queries better.

---

## 8. Gradio for GUI

**Decision:** Use Gradio (Blocks API) for the frontend rather than React/Vue.

**Rationale:**
- Fast to implement with rich components (dataframes, tabs, markdown, HTML)
- Python-native — no separate npm build step
- Easily containerised
- Sufficient for the demo and evaluation

**Trade-off:** Not suitable for production-grade UI. React would provide better state management and UX.
