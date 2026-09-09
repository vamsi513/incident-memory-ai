"""
scripts/build_pgvector_index.py — Loads data/processed/chunks.json (the same
chunk file build_index.py uses for FAISS) into the pgvector-backed
document_chunks table, as an alternative dense-retrieval backend.

Requires the pgvector-enabled Postgres container running (docker compose up
postgres) with scripts/sql/init_pgvector.sql already applied.

Usage:
    python -m scripts.build_pgvector_index
"""

import json
from pathlib import Path

from retrieval.embedder import Embedder
from retrieval.pgvector_store import PgVectorStore


def main() -> None:
    chunk_path = Path("data/processed/chunks.json")
    if not chunk_path.exists():
        raise FileNotFoundError(
            "Missing data/processed/chunks.json. Run ingestion first with: python -m scripts.run_ingestion"
        )

    chunks = json.loads(chunk_path.read_text(encoding="utf-8"))
    if not chunks:
        raise ValueError("No chunks found in data/processed/chunks.json")

    texts = [chunk["text"] for chunk in chunks]

    print(f"Loaded {len(chunks)} chunks")
    print("Loading embedding model...")
    embedder = Embedder()

    print("Encoding chunks...")
    embeddings = embedder.encode(texts)
    print(f"Embedding dimension: {len(embeddings[0])}")

    store = PgVectorStore()
    store.clear()
    store.add(embeddings=embeddings, records=chunks)
    count = store.count()
    store.close()

    print(f"Inserted {count} rows into document_chunks")
    if count != len(chunks):
        raise AssertionError(f"Expected {len(chunks)} rows, found {count} -- ingestion did not complete correctly")


if __name__ == "__main__":
    main()
