import json
from pathlib import Path

from retrieval.embedder import Embedder
from retrieval.vector_store import FaissStore


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

    dim = len(embeddings[0])
    print(f"Embedding dimension: {dim}")

    store = FaissStore(dim=dim)
    store.add(embeddings=embeddings, records=chunks)
    store.save("data/processed")

    print("Saved FAISS index to data/processed/index.faiss")
    print("Saved metadata to data/processed/index_records.json")


if __name__ == "__main__":
    main()

