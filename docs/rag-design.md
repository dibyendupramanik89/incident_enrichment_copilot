# RAG Design — Incident & Ticket Enrichment Copilot

## Overview

The RAG pipeline uses dense vector retrieval with a local ChromaDB vector store and the `nomic-embed-text` embedding model. Documents are chunked, embedded with the Nomic embedding model (via Ollama or the nomic client), and stored in ChromaDB for fast cosine-similarity search.

**Design rationale:** Dense embeddings + a lightweight vector DB improve semantic retrieval for short, diverse operational documents while remaining easy to run locally (Ollama or nomic) and portable to hosted embedding services if needed.

---

## Source Document Types

| Document | Type | Relevance |
|---|---|---|
| `alarm_response_playbook.md` | Procedure manual | Alarm response steps by severity and type |
| `faq.md` | Knowledge base | Common operator questions about investigation and ticketing |
| `historical_resolutions.md` | Case notes | Past incident resolutions (INC-1001 to INC-1005) |
| `incident_enrichment_overview.md` | Architecture doc | System design, workflow, priority scoring model |
| `operating_procedures.md` | Technical spec | Equipment normal ranges, alarm setpoints, trip values |
| `troubleshooting_guide.md` | Troubleshooting tree | BFP, compressor, motor fault diagnosis procedures |

---

## Ingestion Flow

```
rag/documents/  ──[read .md/.txt files]──►  text
                                              │
                                         [chunk_text()]
                                         ~800–900 chars/chunk
                                         ~150 char overlap
                                              │
                                   [embed with nomic-embed-text]
                                vector dim: model-dependent (e.g. 768)
                                              │
                                         [upsert into ChromaDB]
                                         collection: "rag_corpus"
```

**Run ingestion (embeddings → ChromaDB):**
```bash
# Ensure Ollama (or nomic client) is available and reachable
# Example (Ollama): start Ollama, then run the local ingest which calls the embedding model
.venv/bin/python rag/ingestion/ingest.py
```

**Output:**
```
  Embedding alarm_response_playbook.md: 10 chunks... done
  Embedding faq.md: 8 chunks... done
  Embedding historical_resolutions.md: 13 chunks... done
  Embedding incident_enrichment_overview.md: 8 chunks... done
  Embedding operating_procedures.md: 10 chunks... done
  Embedding troubleshooting_guide.md: 11 chunks... done
  Ingestion complete. 60 chunks stored in ChromaDB (collection: rag_corpus)
```

---

## Chunking Strategy

| Parameter | Value | Rationale |
|---|---|---|
| Chunk size | 800–900 characters | Fits in context window while keeping coherent procedure steps |
| Overlap | 150 characters | Prevents splitting sentences at chunk boundaries |
| Chunk ID | `{source}::chunk_{n}` | Enables deduplication and source attribution |
| Metadata | source, section (first line), length, text_hash | Enables citation, freshness checks and de-duplication |

---

## Text Extraction

Plain text extraction from markdown files using Python `str.read_text()`. No PDF parser or HTML extractor needed — all documents are already in `.md` format.

---

## Retrieval Method: Dense Embedding Search (ChromaDB)

**Algorithm:** Semantic search using `nomic-embed-text` embeddings stored in ChromaDB. Queries are embedded with the same model and results are ranked by cosine similarity.

**Parameters:**
- `embedding_model = nomic-embed-text` (via Ollama or nomic client)
- `vector_store = ChromaDB` (local collection: `rag_corpus`)
- `top_k = 4` (candidate documents returned per query)
- `MIN_SIMILARITY = 0.12` (optional cutoff; tuned on small corpus)

**Scoring:**
Cosine similarity between normalized query vector q and chunk vector d:

$$\text{sim}(q,d) = \frac{q \cdot d}{\|q\| \, \|d\|}$$

Similarity scores are optionally re-scaled into a [0,1] range for display and combined with other signals (e.g., ticket-matching score, alarm metadata) for final confidence.

---

## Retrieval Filters

| Filter | Value | Where applied |
|---|---|---|
| Minimum score | 0.10 | After normalisation, before returning results |
| Top-k | 4 | Maximum results per query |

---

## Hybrid Search

Hybrid search (sparse BM25 + dense embeddings) is supported conceptually and can be enabled if desired. For the current corpus (≈60 chunks) dense retrieval with ChromaDB provides strong semantic matches; hybrid approaches are recommended when merging very large corpora or when exact term matches must be prioritized.

---

## Ranking / Reranking

Initial ranking is by cosine similarity from ChromaDB (highest → lowest). An optional reranker (LLM-based or lightweight heuristic) can re-score the top-k candidates by relevance to the query, presence of alarm keywords, or timestamp/freshness.

---

## Citation Construction

Each retrieved chunk is returned as:
```json
{
     "source": "alarm_response_playbook.md",
     "content": "...(chunk text)...",
     "score": 0.85,                # cosine similarity (or normalized score)
     "chunk_id": "alarm_response_playbook.md::chunk_3",
     "vector_id": "uuid-or-hash",
     "metadata": { "section": "...", "length": 123 }
}
```

Citations are displayed in the **RAG Citations** tab of the Gradio UI as a table with Source, Score, and Content Snippet columns.

---

## Low-Confidence Handling

Two layers:

1. **Retrieval layer:** Chunks with score < 0.10 are excluded.
2. **Output guardrail layer:** `OutputGuardrails._confidence_score()` combines:
   - Average RAG relevance score (max 0.30 contribution)
   - RAG result count (max 0.20 contribution)
   - Alarm data presence (max 0.30 contribution)
   - Answer word count (max 0.20 contribution)
   
   If the composite score < 0.40, a caveat is appended to the answer:
   > ⚠️ **Low confidence**: The above is based on limited evidence. Verify with on-site inspection before taking action.

---

## Prompt Injection Protections

The RAG pipeline protects against prompt injection embedded inside retrieved documents in two ways:

1. **Pre-retrieval (input guardrails):** The user query is checked for injection patterns before retrieval begins. Injected queries never reach the retrieval pipeline.

2. **Retrieved content framing:** Each chunk is wrapped in a clearly labelled context block before being passed to the LLM:
   ```
   [SOURCE: alarm_response_playbook.md | Score: 0.85]
   <chunk content>
   ```
   The LLM system prompt instructs it to treat this block as reference data, not as instructions.

3. **Output validation:** The output guardrail checks for instruction-like phrases (`"ignore previous"`, `"you are now"`) in the answer — these would indicate a successful injection via retrieved content.

---

## Index Refresh Process

The vector index is stored in a local ChromaDB collection (default: `rag_corpus`). To rebuild after adding or modifying documents:

```bash
# Ensure Ollama (or nomic client) is running and reachable; then:
.venv/bin/python rag/ingestion/ingest.py
```

The backend's `RAGRetriever` loads vectors from ChromaDB at startup. After a refresh, restart the backend service or call `retriever.reload()` to refresh the in-memory cache.

---

## Example Retrieved Chunks

**Query:** `BFP-101 low suction pressure critical alarm`

| Source | Score | Content Snippet |
|---|---|---|
| `incident_enrichment_overview.md` | 1.00 | `| BFP-101 | Boiler Feed Pump | Critical | Unit 1 |...` |
| `historical_resolutions.md` | 0.91 | `# Historical Incident Resolutions — INC-1001 BFP-101 low suction pressure...` |
| `troubleshooting_guide.md` | 0.74 | `# Troubleshooting Guide — Boiler Feed Pump: Step 1 Check suction strainer...` |
| `alarm_response_playbook.md` | 0.68 | `## Low Suction Pressure — Response: immediate isolation if below -0.5 bar...` |
