"""
RAG retriever adapter — delegates to the shared rag/retrieval/retriever module.
Falls back to an inline BM25 retriever when the module is not importable
(e.g., inside Docker where the rag/ tree may be mounted separately).
"""
from __future__ import annotations

import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

# Try to import from rag/retrieval first (full module path)
_rag_retriever_path = str(Path(__file__).resolve().parents[2] / "rag" / "retrieval")
if _rag_retriever_path not in sys.path:
    sys.path.insert(0, _rag_retriever_path)

try:
    from retriever import RAGRetriever  # noqa: F401 — re-export
except ImportError:
    # Inline BM25 fallback (pure-Python, zero extra deps)
    _DOCS_DIR = Path(__file__).resolve().parents[2] / "rag" / "documents"
    _BM25_K1 = 1.5
    _BM25_B = 0.75
    _MIN_SCORE = 0.10

    def _tok(text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9\-]{2,}", text.lower())

    def _chunks_from_dir(docs_dir: Path) -> tuple[List[Dict], Dict[str, int], float]:
        chunks: List[Dict] = []
        if not docs_dir.exists():
            return chunks, {}, 0.0
        for path in sorted(docs_dir.glob("**/*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            raw = path.read_text(encoding="utf-8").strip()
            start = 0
            while start < len(raw):
                end = min(len(raw), start + 900)
                snippet = raw[start:end].strip()
                if snippet:
                    chunks.append({"source": path.name, "content": snippet,
                                   "length": len(_tok(snippet))})
                if end == len(raw):
                    break
                start = max(0, end - 150)
        tdf: Dict[str, int] = defaultdict(int)
        for c in chunks:
            for t in set(_tok(c["content"])):
                tdf[t] += 1
        avg = sum(c["length"] for c in chunks) / max(1, len(chunks))
        return chunks, dict(tdf), avg

    class RAGRetriever:  # type: ignore[no-redef]
        def __init__(self, documents_dir: str | None = None):
            env = os.getenv("RAG_DOCUMENTS_DIR")
            dd = Path(documents_dir or env or str(_DOCS_DIR))
            self._chunks, self._tdf, self._avg = _chunks_from_dir(dd)
            self._N = len(self._chunks)

        def retrieve(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
            if not self._chunks or not query.strip():
                return []
            qt = _tok(query)
            scored: List[tuple[float, Dict]] = []
            for chunk in self._chunks:
                tf = Counter(_tok(chunk["content"]))
                dl = chunk["length"]
                score = 0.0
                for term in qt:
                    df = self._tdf.get(term, 0)
                    if df == 0:
                        continue
                    idf = math.log((self._N - df + 0.5) / (df + 0.5) + 1.0)
                    freq = tf.get(term, 0)
                    tfn = (freq * (_BM25_K1 + 1.0)) / (
                        freq + _BM25_K1 * (1.0 - _BM25_B + _BM25_B * dl / max(1, self._avg))
                    )
                    score += idf * tfn
                if score > 0:
                    scored.append((score, chunk))
            if not scored:
                return []
            scored.sort(key=lambda x: x[0], reverse=True)
            top = scored[0][0]
            return [
                {"source": c["source"], "content": c["content"], "score": round(s / top, 4)}
                for s, c in scored[:k]
                if (s / top) >= _MIN_SCORE
            ]
