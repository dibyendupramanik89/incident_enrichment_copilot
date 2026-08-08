# RAG Design — Incident & Ticket Enrichment Copilot

## Overview

The RAG pipeline uses **BM25** (Best Match 25) — a classical term-frequency based retrieval algorithm implemented in pure Python. No embedding model, no vector database, no external ML service is required.

**Design rationale:** For a corpus of 60 chunks across 6 documents, BM25 provides fast, deterministic, and fully auditable retrieval. It is sufficient for the scope of this use case and removes all infrastructure complexity.

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
                                         900 chars/chunk
                                         150 char overlap
                                              │
                                         [tokenise()]
                                         regex: [a-zA-Z0-9\-]{2,}
                                         lowercased
                                              │
                                         [compute term_doc_freq]
                                         count documents containing each term
                                              │
                                         [serialise to JSON]
                                         rag/.index/index.json
```

**Run ingestion:**
```bash
python rag/ingestion/ingest.py
```

**Output:**
```
  Indexed alarm_response_playbook.md: 10 chunks
  Indexed faq.md: 8 chunks
  Indexed historical_resolutions.md: 13 chunks
  Indexed incident_enrichment_overview.md: 8 chunks
  Indexed operating_procedures.md: 10 chunks
  Indexed troubleshooting_guide.md: 11 chunks
Index saved → rag/.index/index.json
  Total chunks: 60
```

---

## Chunking Strategy

| Parameter | Value | Rationale |
|---|---|---|
| Chunk size | 900 characters | Fits in context window while keeping coherent procedure steps |
| Overlap | 150 characters | Prevents splitting sentences at chunk boundaries |
| Chunk ID | `{source}::chunk_{n}` | Enables deduplication and source attribution |
| Metadata | source, section (first line), length | Enables citation and relevance filtering |

---

## Text Extraction

Plain text extraction from markdown files using Python `str.read_text()`. No PDF parser or HTML extractor needed — all documents are already in `.md` format.

---

## Retrieval Method: BM25

**Algorithm:** BM25 (Robertson & Spärck Jones, 1976)

**Parameters:**
- `k1 = 1.5` (term frequency saturation)
- `b = 0.75` (document length normalisation)
- `MIN_SCORE = 0.10` (minimum normalised score to include in results)

**Scoring formula:**

$$\text{BM25}(d, q) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t, d) \cdot (k_1 + 1)}{f(t, d) + k_1 \cdot (1 - b + b \cdot \frac{|d|}{\text{avgdl}})}$$

Where:
- $\text{IDF}(t) = \log\left(\frac{N - df(t) + 0.5}{df(t) + 0.5} + 1\right)$
- $f(t, d)$ = term frequency in document chunk
- $|d|$ = chunk length in tokens
- $\text{avgdl}$ = average chunk length across corpus
- $N$ = total number of chunks (60)

**Score normalisation:** All scores normalised by the top result score → range [0, 1].

---

## Retrieval Filters

| Filter | Value | Where applied |
|---|---|---|
| Minimum score | 0.10 | After normalisation, before returning results |
| Top-k | 4 | Maximum results per query |

---

## Hybrid Search

Not implemented. BM25 alone is sufficient for the 60-chunk corpus. A hybrid approach (BM25 + dense embedding) would be considered at corpus sizes > 10,000 chunks.

---

## Ranking / Reranking

Results are ranked by BM25 score (descending). No reranking step — the BM25 score is directly used as the citation relevance score displayed in the GUI.

---

## Citation Construction

Each retrieved chunk is returned as:
```json
{
  "source": "alarm_response_playbook.md",
  "content": "...(chunk text)...",
  "score": 0.85,
  "chunk_id": "alarm_response_playbook.md::chunk_3"
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

The index is a flat JSON file at `rag/.index/index.json`. To rebuild:

```bash
# After adding or modifying documents in rag/documents/
python rag/ingestion/ingest.py
```

The backend's `RAGRetriever` loads the index at startup. After a refresh, restart the backend service (or call `retriever.reload()` programmatically).

---

## Example Retrieved Chunks

**Query:** `BFP-101 low suction pressure critical alarm`

| Source | Score | Content Snippet |
|---|---|---|
| `incident_enrichment_overview.md` | 1.00 | `| BFP-101 | Boiler Feed Pump | Critical | Unit 1 |...` |
| `historical_resolutions.md` | 0.91 | `# Historical Incident Resolutions — INC-1001 BFP-101 low suction pressure...` |
| `troubleshooting_guide.md` | 0.74 | `# Troubleshooting Guide — Boiler Feed Pump: Step 1 Check suction strainer...` |
| `alarm_response_playbook.md` | 0.68 | `## Low Suction Pressure — Response: immediate isolation if below -0.5 bar...` |
