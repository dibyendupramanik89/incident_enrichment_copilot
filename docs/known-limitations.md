# Known Limitations

## Current Gaps

### RAG

| Limitation | Impact | Mitigation |
|---|---|---|
| BM25 is lexical only | Misses semantic matches ("pump failure" vs "impeller degradation") | Add embedding layer for hybrid search |
| 60 chunks from 6 documents | Limited coverage of the knowledge domain | Expand corpus with real manuals |
| No re-indexing trigger | Must manually run `ingest.py` after doc changes | Add file-watcher or webhook to auto-rebuild |
| No chunk-level metadata filtering | Cannot filter RAG results by date or document type | Add metadata to index schema |

### Ticketing

| Limitation | Impact | Mitigation |
|---|---|---|
| In-memory store | Tickets lost on service restart | Add SQLite or PostgreSQL backend |
| Mock only | Not integrated with real Jira/ServiceNow | Add OAuth2 + Jira REST client |
| No ticket deduplication | Duplicate tickets could be created for the same alarm | Add alarm_id uniqueness check |

### Orchestration

| Limitation | Impact | Mitigation |
|---|---|---|
| No conversation memory | Each query starts fresh — no context from prior turns | Add session store (Redis or in-memory) |
| Fixed 9-step pipeline | Cannot handle queries outside the defined intents gracefully | Add LLM agent loop for open-ended queries |
| Asset extraction is keyword-based | Fails for novel asset names not in the keyword list | Use LLM NER or MCP `search_asset` with fallback |
| Priority scoring uses mock data | Scores are deterministic (not AI-driven) in the simulator | Wire to real ML model |

### MCP

| Limitation | Impact | Mitigation |
|---|---|---|
| HTTP JSON-RPC only | Not compatible with stdio-transport MCP clients (Claude Desktop) | Add stdio adapter or use official MCP SDK |
| No tool output validation | MCP server does not validate Alarm API response schema | Add Pydantic response models |
| No circuit breaker | Repeated failures exhaust retries | Add tenacity or circuit breaker pattern |

### Security

| Limitation | Impact | Mitigation |
|---|---|---|
| Static bearer token | `demo-token` is hardcoded as default | Use OAuth2 or API key rotation |
| No HTTPS in local mode | Traffic is plaintext | Add TLS termination (nginx/Caddy) |
| No rate limiting | Backend API has no rate limiter | Add slowapi or nginx rate limiting |
| Gradio has no auth | Anyone with the URL can access the UI | Add `gr.Auth` or OAuth2 |

### Testing

| Limitation | Impact | Mitigation |
|---|---|---|
| Test suite is scaffolded only | No automated test coverage | Implement all tests per submission spec |
| No CI/CD pipeline | Tests not run on commit | Add `.github/workflows/ci.yml` |
| No coverage report | Cannot measure test completeness | Add pytest-cov |

### Deployment

| Limitation | Impact | Mitigation |
|---|---|---|
| No CI/CD included | No automatic build/test/deploy | Add GitHub Actions workflow |
| No demo video | Evaluators must run locally | Record and link a Loom/YouTube demo |
| BM25 index not committed to git | Must be rebuilt after clone | Either commit index or add `make rag-index` to Docker build |
| Docker not tested end-to-end | `docker compose up --build` may have path issues | Test on a fresh Linux VM |

---

## Future Improvements

1. **Semantic RAG** — Add sentence-transformers + FAISS for hybrid BM25 + dense retrieval
2. **Real LLM planning** — Replace fixed pipeline with a ReAct/function-calling agent loop
3. **Persistent storage** — Add PostgreSQL for tickets and sessions
4. **Real ticketing integration** — Add Jira REST API client with OAuth2
5. **Conversation memory** — Add Redis session store for multi-turn dialogue
6. **Streaming responses** — Stream LLM output to Gradio using `gr.ChatInterface` streaming mode
7. **Alarm trend charts** — Add Plotly charts in the Gradio UI for alarm trend data
8. **Multi-tenant auth** — Add Keycloak/Auth0 for operator identity and role-based access
9. **Observability** — Add OpenTelemetry traces, Prometheus metrics, Grafana dashboard
10. **CI/CD** — GitHub Actions: lint → test → build Docker images → push to GHCR
