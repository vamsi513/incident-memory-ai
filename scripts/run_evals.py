import asyncio
import json
import subprocess
import time
from datetime import date
from pathlib import Path

import mlflow

from core.config import settings
from evals.metrics import hit_rate_at_k, reciprocal_rank
from schemas.search import SearchRequest
from services.bm25_service import BM25Service
from services.hybrid_search_service import HybridSearchService
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService


def _git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


async def _run_all(examples: list[dict]) -> tuple[list[dict], list[float], list[float], list[float], list[float], list[float]]:
    service = HybridSearchService(
        bm25_service=BM25Service(),
        vector_service=VectorSearchService(),
        rerank_service=RerankService(),
        parent_retrieval_service=ParentRetrievalService(),
    )

    hit_rate_1_scores: list[float] = []
    hit_rate_3_scores: list[float] = []
    hit_rate_5_scores: list[float] = []
    mrr_scores: list[float] = []
    latencies_ms: list[float] = []
    per_query_data: list[dict] = []

    for example in examples:
        query = example["query"]
        expected_doc_ids = example["expected_doc_ids"]

        t0 = time.perf_counter()
        response = await service.search(SearchRequest(query=query, top_k=5))
        latency_ms = (time.perf_counter() - t0) * 1000

        retrieved_doc_ids = [result.parent_id for result in response.results]

        r1 = hit_rate_at_k(retrieved_doc_ids, expected_doc_ids, k=1)
        r3 = hit_rate_at_k(retrieved_doc_ids, expected_doc_ids, k=3)
        r5 = hit_rate_at_k(retrieved_doc_ids, expected_doc_ids, k=5)
        rr = reciprocal_rank(retrieved_doc_ids, expected_doc_ids)

        hit_rate_1_scores.append(r1)
        hit_rate_3_scores.append(r3)
        hit_rate_5_scores.append(r5)
        mrr_scores.append(rr)
        latencies_ms.append(latency_ms)

        per_query_data.append({
            "query": query,
            "expected": expected_doc_ids,
            "retrieved": retrieved_doc_ids,
            "hit_rate_at_1": r1,
            "hit_rate_at_3": r3,
            "hit_rate_at_5": r5,
            "reciprocal_rank": rr,
            "latency_ms": round(latency_ms, 2),
        })

        print(f"Query: {query}")
        print(f"Expected: {expected_doc_ids}")
        print(f"Retrieved: {retrieved_doc_ids}")
        print(f"HitRate@1: {r1:.2f}  HitRate@3: {r3:.2f}  HitRate@5: {r5:.2f}  MRR: {rr:.2f}  Latency: {latency_ms:.1f}ms")
        print("-" * 60)

    return per_query_data, hit_rate_1_scores, hit_rate_3_scores, hit_rate_5_scores, mrr_scores, latencies_ms


def main() -> None:
    dataset_path = Path("evals/dataset.json")
    examples = json.loads(dataset_path.read_text(encoding="utf-8"))

    print("\n=== Retrieval Evaluation ===\n")

    (
        per_query_data,
        hit_rate_1_scores,
        hit_rate_3_scores,
        hit_rate_5_scores,
        mrr_scores,
        latencies_ms,
    ) = asyncio.run(_run_all(examples))

    n = len(examples)
    avg_r1 = sum(hit_rate_1_scores) / n
    avg_r3 = sum(hit_rate_3_scores) / n
    avg_r5 = sum(hit_rate_5_scores) / n
    avg_mrr = sum(mrr_scores) / n
    avg_latency = sum(latencies_ms) / n

    print("\n=== Aggregate Metrics ===")
    print(f"Average HitRate@1: {avg_r1:.2f}")
    print(f"Average HitRate@3: {avg_r3:.2f}")
    print(f"Average HitRate@5: {avg_r5:.2f}")
    print(f"Average MRR:      {avg_mrr:.2f}")
    print(f"Avg Latency/query:{avg_latency:.1f}ms")

    mlflow.set_experiment("incident-memory-retrieval-eval")

    with mlflow.start_run(run_name=f"eval-{date.today()}"):
        mlflow.log_params({
            "embed_model": settings.embed_model,
            "rerank_model": settings.rerank_model,
            "retrieval_strategy": "hybrid_bm25_dense_rrf_rewrite_inject_boost_rerank",
            "top_k": 5,
            "num_queries": n,
            "eval_date": str(date.today()),
            "git_sha": _git_sha(),
        })

        mlflow.log_metrics({
            "avg_hit_rate_at_1": avg_r1,
            "avg_hit_rate_at_3": avg_r3,
            "avg_hit_rate_at_5": avg_r5,
            "avg_mrr": avg_mrr,
            "avg_latency_ms": avg_latency,
        })

        for i, row in enumerate(per_query_data):
            mlflow.log_metrics({
                f"q{i}_hit_rate_at_1": row["hit_rate_at_1"],
                f"q{i}_hit_rate_at_3": row["hit_rate_at_3"],
                f"q{i}_hit_rate_at_5": row["hit_rate_at_5"],
                f"q{i}_reciprocal_rank": row["reciprocal_rank"],
                f"q{i}_latency_ms": row["latency_ms"],
            })

        mlflow.log_text(json.dumps(per_query_data, indent=2), "per_query_results.json")

    print("\nMLflow run logged — start the UI with: mlflow ui")


if __name__ == "__main__":
    main()
