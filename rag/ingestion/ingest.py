"""
RAG ingestion pipeline — ChromaDB + Ollama embeddings.

Loads documents from rag/documents/, chunks them, embeds each chunk using
Ollama's nomic-embed-text model, and stores them in a persistent ChromaDB
collection at rag/.chromadb/.

Usage:
    python rag/ingestion/ingest.py

Requires:
    - Ollama running:  ollama serve
    - Model pulled:    ollama pull nomic-embed-text
    - chromadb installed: uv pip install chromadb
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import chromadb
import requests

DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"
CHROMA_DIR = Path(__file__).resolve().parent.parent / ".chromadb"
COLLECTION_NAME = "rag_documents"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


# ── Chunker ───────────────────────────────────────────────────────────────────
def chunk_text(text: str, source: str) -> List[Dict[str, Any]]:
    text = text.strip()
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(len(text), start + CHUNK_SIZE)
        snippet = text[start:end].strip()
        if snippet:
            first_line = snippet.split("\n")[0].strip().lstrip("#").strip()
            chunks.append({
                "chunk_id": f"{source}::chunk_{idx}",
                "source": source,
                "section": first_line[:80] if first_line else source,
                "content": snippet,
            })
            idx += 1
        if end == len(text):
            break
        start = max(0, end - CHUNK_OVERLAP)
    return chunks


# ── Ollama embedding ──────────────────────────────────────────────────────────
def embed(text: str) -> List[float]:
    """Call Ollama /api/embeddings to get a vector for text."""
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


# ── Main ingestion ─────────────────────────────────────────────────────────────
def ingest(documents_dir: Path, chroma_dir: Path) -> None:
    client = chromadb.PersistentClient(path=str(chroma_dir))

    # Drop and recreate collection for a clean rebuild
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Dropped existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    total = 0
    for path in sorted(documents_dir.glob("**/*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
            continue
        raw = path.read_text(encoding="utf-8")
        chunks = chunk_text(raw, path.name)
        if not chunks:
            continue

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [{"source": c["source"], "section": c["section"]} for c in chunks]

        print(f"  Embedding {path.name} ({len(chunks)} chunks)...", end=" ", flush=True)
        embeddings = [embed(doc) for doc in documents]
        print("done")

        collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        total += len(chunks)

    print(f"\nIngestion complete. {total} chunks stored in ChromaDB at {chroma_dir}")
    print(f"Collection: '{COLLECTION_NAME}'")


if __name__ == "__main__":
    print(f"Ollama embedding model: {EMBED_MODEL} at {OLLAMA_BASE_URL}")
    print(f"Documents dir: {DOCUMENTS_DIR}")
    ingest(DOCUMENTS_DIR, CHROMA_DIR)

