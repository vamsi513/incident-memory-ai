import json
from pathlib import Path

from rerank.cross_encoder import Reranker
from retrieval.bm25_store import BM25Store
from retrieval.embedder import Embedder
from retrieval.hybrid import reciprocal_rank_fusion
from retrieval.vector_store import FaissStore


def main() -> None:
    query = "What fixed the checkout timeout incident?"

    records_path = Path("data/processed/index_records.json")
    if not records_path.exists():
        raise FileNotFoundError(
            "Missing data/processed/index_records.json. Run: python -m scripts.build_index"
        )

    records = json.loads(records_path.read_text(encoding="utf-8"))

    embedder = Embedder()
    vector_store = FaissStore.load("data/processed")

    query_embedding = embedder.encode([query])[0]
    vector_results = vector_store.search(query_embedding=query_embedding, top_k=8)

    bm25_store = BM25Store(
        texts=[record["text"] for record in records],
        records=records,
    )
    bm25_results = bm25_store.search(query=query, top_k=8)

    hybrid_results = reciprocal_rank_fusion([vector_results, bm25_results])[:8]

    reranker = Reranker()
    reranked_results = reranker.rerank(query=query, records=hybrid_results, top_n=5)

    print(f"\nQuery: {query}\n")

    print("=== Hybrid Results Before Rerank ===")
    for i, result in enumerate(hybrid_results, start=1):
        print(f"{i}. {result['title']} | {result['section']} | hybrid_score={result['hybrid_score']:.6f}")
        print(result["text"])
        print("-" * 60)

    print("\n=== Results After Rerank ===")
    for i, result in enumerate(reranked_results, start=1):
        print(f"{i}. {result['title']} | {result['section']} | rerank_score={result['rerank_score']:.6f}")
        print(result["text"])
        print("-" * 60)


if __name__ == "__main__":
    main()

