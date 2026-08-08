"""
RAG retrieval module — ChromaDB + Ollama embeddings.

Queries the persistent ChromaDB collection built by rag/ingestion/ingest.py.
Falls back to BM25 (in-memory) if ChromaDB or Ollama is unavailable.

Usage:
    from rag.retrieval.retriever import RAGRetriever
    r = RAGRetriever()
    results = r.retrieve("BFP-101 low suction pressure", k=4)
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"
CHROMA_DIR = Path(__file__).resolve().parent.parent / ".chromadb"
COLLECTION_NAME = "rag_documents"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

BM25_K1 = 1.5
BM25_B = 0.75
MIN_SCORE = 0.10


def _tokenise(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9\-]{2,}", text.lower())


def _embed(text: str) -> List[float]:
    import requests
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


class RAGRetriever:
    """
    ChromaDB-backed semantic retriever.
    Falls back to BM25 if ChromaDB collection is not found or Ollama is down.
    """

    def __init__(self, documents_dir: str | None = None):
        env_docs = os.getenv("RAG_DOCUMENTS_DIR")
        self._docs_dir = Path(documents_dir or env_docs or str(DOCUMENTS_DIR))
        self._chroma_dir = CHROMA_DIR
        self._collection = None
        self._N = 0

        # BM25 fallback state
        self._chunks: List[Dict[str, Any]] = []
        self._term_doc_freq: Dict[str, int] = {}
        self._avg_len = 0.0

        self._load()

    def _load(self) -> None:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(self._chroma_dir))
            self._collection = client.get_collection(COLLECTION_NAME)
            self._N = self._collection.count()
            print(f"[RAG] ChromaDB loaded — {self._N} chunks in '{COLLECTION_NAME}'")
        except Exception as e:
            print(f"[RAG] ChromaDB not available ({e}), falling back to BM25")
            self._collection = None
            self._build_bm25_fallback()

    def _build_bm25_fallback(self) -> None:
        if not self._docs_dir.exists():
            return
        all_chunks: List[Dict[str, Any]] = []
        for path in sorted(self._docs_dir.glob("**/*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            raw = path.read_text(encoding="utf-8")
            text = raw.strip()
            start, idx = 0, 0
            while start < len(text):
                end = min(len(text), start + 900)
                snippet = text[start:end].strip()
                if snippet:
                    all_chunks.append({
                        "chunk_id": f"{path.name}::chunk_{idx}",
                        "source": path.name,
                        "content": snippet,
                        "length": len(_tokenise(snippet)),
                    })
                    idx += 1
                if end == len(text):
                    break
                start = max(0, end - 150)

        tdf: Dict[str, int] = defaultdict(int)
        for c in all_chunks:
            for t in set(_tokenise(c["content"])):
                tdf[t] += 1
        self._chunks = all_chunks
        self._term_doc_freq = dict(tdf)
        self._N = len(all_chunks)
        self._avg_len = sum(c["length"] for c in all_chunks) / max(1, self._N)

    def _bm25(self, query_tokens: List[str], chunk: Dict[str, Any]) -> float:
        tf = Counter(_tokenise(chunk["content"]))
        doc_len = chunk.get("length", len(tf))
        score = 0.0
        for term in query_tokens:
            df = self._term_doc_freq.get(term, 0)
            if df == 0:
                continue
            idf = math.log((self._N - df + 0.5) / (df + 0.5) + 1.0)
            freq = tf.get(term, 0)
            tf_norm = (freq * (BM25_K1 + 1.0)) / (
                freq + BM25_K1 * (1.0 - BM25_B + BM25_B * doc_len / max(1, self._avg_len))
            )
            score += idf * tf_norm
        return score

    def retrieve(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Return top-k semantically similar chunks."""
        if not query.strip():
            return []

        # ChromaDB semantic retrieval
        if self._collection is not None:
            try:
                vec = _embed(query)
                res = self._collection.query(
                    query_embeddings=[vec],
                    n_results=min(k, self._N),
                    include=["documents", "metadatas", "distances"],
                )
                results = []
                for doc, meta, dist in zip(
                    res["documents"][0], res["metadatas"][0], res["distances"][0]
                ):
                    score = round(1.0 - dist, 4)
                    results.append({
                        "source": meta.get("source", ""),
                        "content": doc,
                        "score": score,
                        "chunk_id": meta.get("section", ""),
                    })
                return results
            except Exception as e:
                print(f"[RAG] ChromaDB query failed ({e}), falling back to BM25")

        # BM25 fallback
        if not self._chunks:
            return []
        query_tokens = _tokenise(query)
        scored = [(self._bm25(query_tokens, c), c) for c in self._chunks]
        scored = [(s, c) for s, c in scored if s > 0]
        if not scored:
            return []
        scored.sort(key=lambda x: x[0], reverse=True)
        max_score = scored[0][0]
        return [
            {"source": c["source"], "content": c["content"],
             "score": round(s / max_score, 4), "chunk_id": c["chunk_id"]}
            for s, c in scored[:k]
            if round(s / max_score, 4) >= MIN_SCORE
        ]

    def reload(self) -> None:
        self._collection = None
        self._chunks = []
        self._N = 0
        self._load()
