import json
from pathlib import Path

from retrieval.bm25_store import BM25Store
from retrieval.embedder import Embedder
from retrieval.hybrid import reciprocal_rank_fusion
from retrieval.query_rewrite import rewrite_query
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
    bm25_store = BM25Store(
        texts=[record["text"] for record in records],
        records=records,
    )

    all_result_sets = []
    rewritten_queries = rewrite_query(query)

    for rewritten_query in rewritten_queries:
        query_embedding = embedder.encode([rewritten_query])[0]
        vector_results = vector_store.search(query_embedding=query_embedding, top_k=5)
        bm25_results = bm25_store.search(query=rewritten_query, top_k=5)
        all_result_sets.append(vector_results)
        all_result_sets.append(bm25_results)

    hybrid_results = reciprocal_rank_fusion(all_result_sets)[:5]

    print(f"\nOriginal Query: {query}\n")
    print("Rewritten Queries:")
    for rq in rewritten_queries:
        print(f"- {rq}")

    print("\n=== Hybrid Results ===")
    for i, result in enumerate(hybrid_results, start=1):
        print(f"{i}. {result['title']} | {result['section']} | score={result['hybrid_score']:.6f}")
        print(result["text"])
        print("-" * 50)


if __name__ == "__main__":
    main()

