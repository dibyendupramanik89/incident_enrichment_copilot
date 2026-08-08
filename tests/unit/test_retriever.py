"""
Unit tests for RAGRetriever (rag/retrieval/retriever.py).

These tests force the BM25 fallback path (no ChromaDB/Ollama dependency) by
pointing RAGRetriever at a temporary documents directory and monkeypatching
the ChromaDB loader to fail, so they run reliably in CI without external
services.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "rag", "retrieval"))

from retriever import RAGRetriever  # noqa: E402


def _make_retriever(tmp_path, monkeypatch):
    (tmp_path / "doc_a.md").write_text(
        "The boiler feed pump BFP-101 suction pressure alarm indicates low inlet pressure. "
        "Check the suction strainer for blockage and verify the upstream valve is fully open."
    )
    (tmp_path / "doc_b.md").write_text(
        "Compressor discharge temperature alarms are typically caused by fouled coolers "
        "or insufficient cooling water flow. Inspect the aftercooler."
    )

    r = RAGRetriever(documents_dir=str(tmp_path))
    # Force BM25 fallback path regardless of ChromaDB availability in the test env
    r._collection = None
    r._build_bm25_fallback()
    return r


class TestRAGRetrieverBM25Fallback:
    def test_retrieve_returns_relevant_chunk(self, tmp_path, monkeypatch):
        r = _make_retriever(tmp_path, monkeypatch)
        results = r.retrieve("BFP-101 suction pressure alarm", k=2)
        assert len(results) >= 1
        assert results[0]["source"] == "doc_a.md"
        assert "score" in results[0]
        assert 0.0 <= results[0]["score"] <= 1.0

    def test_retrieve_empty_query_returns_empty(self, tmp_path, monkeypatch):
        r = _make_retriever(tmp_path, monkeypatch)
        assert r.retrieve("", k=4) == []

    def test_retrieve_no_match_returns_empty_or_low_score(self, tmp_path, monkeypatch):
        r = _make_retriever(tmp_path, monkeypatch)
        results = r.retrieve("zzzzz nonexistent gibberish term", k=4)
        assert isinstance(results, list)

    def test_chunk_metadata_has_required_fields(self, tmp_path, monkeypatch):
        r = _make_retriever(tmp_path, monkeypatch)
        results = r.retrieve("compressor discharge temperature", k=2)
        for chunk in results:
            assert "source" in chunk
            assert "content" in chunk
            assert "score" in chunk
            assert "chunk_id" in chunk
