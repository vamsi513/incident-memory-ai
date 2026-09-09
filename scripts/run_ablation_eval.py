"""
scripts/run_ablation_eval.py — Real BM25-only / dense-only / hybrid /
hybrid+reranking comparison across evals/dataset.json.

BM25-only and dense-only use their respective service directly. Hybrid
fuses both via the same RRF logic HybridSearchService uses (no rerank, no
query rewriting, no section injection/boosting -- isolated to just the
fusion step). Hybrid+reranking is the actual, unmodified production
HybridSearchService used by the live API and scripts/run_evals.py.

All four assemble doc-level results via the same ParentRetrievalService
used in production, so results are compared on equal footing.

Usage:
    python -m scripts.run_ablation_eval
    python -m scripts.run_ablation_eval --out results.json
"""

import argparse
import asyncio
import json
import time
from pathlib import Path
from statistics import mean

from evals.metrics import hit_rate_at_k, ndcg_at_k, recall_at_k, reciprocal_rank
from schemas.search import SearchRequest
from services.bm25_service import BM25Service
from services.hybrid_search_service import HybridSearchService
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService

_DATASET_PATH = Path("evals/dataset.json")
_TOP_K = 5


async def _bm25_only(bm25: BM25Service, parent: ParentRetrievalService, query: str) -> list[str]:
    hits = await bm25.search(query, top_k=10)
    results = await parent.assemble(hits)
    return [r.parent_id for r in results[:_TOP_K]]


async def _dense_only(vector: VectorSearchService, parent: ParentRetrievalService, query: str) -> list[str]:
    hits = await vector.search(query, top_k=10)
    results = await parent.assemble(hits)
    return [r.parent_id for r in results[:_TOP_K]]


async def _hybrid_no_rerank(
    bm25: BM25Service, vector: VectorSearchService, parent: ParentRetrievalService, query: str
) -> list[str]:
    bm25_hits = await bm25.search(query, top_k=10)
    vector_hits = await vector.search(query, top_k=10)
    fused = HybridSearchService._fuse_hits([bm25_hits, vector_hits])
    fused = HybridSearchService._dedupe(fused)
    results = await parent.assemble(fused)
    return [r.parent_id for r in results[:_TOP_K]]


async def _hybrid_rerank(service: HybridSearchService, query: str) -> list[str]:
    response = await service.search(SearchRequest(query=query, top_k=_TOP_K))
    return [r.parent_id for r in response.results]


async def _run_all(examples: list[dict]) -> dict[str, list[dict]]:
    bm25 = BM25Service()
    vector = VectorSearchService()
    rerank = RerankService()
    parent = ParentRetrievalService()
    hybrid_service = HybridSearchService(
        bm25_service=bm25, vector_service=vector, rerank_service=rerank, parent_retrieval_service=parent
    )

    configs = {
        "bm25_only": lambda q: _bm25_only(bm25, parent, q),
        "dense_only": lambda q: _dense_only(vector, parent, q),
        "hybrid_no_rerank": lambda q: _hybrid_no_rerank(bm25, vector, parent, q),
        "hybrid_rerank": lambda q: _hybrid_rerank(hybrid_service, q),
    }

    per_config: dict[str, list[dict]] = {name: [] for name in configs}

    for example in examples:
        query = example["query"]
        expected = example["expected_doc_ids"]

        for name, fn in configs.items():
            t0 = time.perf_counter()
            retrieved = await fn(query)
            latency_ms = (time.perf_counter() - t0) * 1000

            per_config[name].append({
                "query": query,
                "expected": expected,
                "retrieved": retrieved,
                "hit_rate_at_5": hit_rate_at_k(retrieved, expected, k=5),
                "recall_at_5": recall_at_k(retrieved, expected, k=5),
                "mrr": reciprocal_rank(retrieved, expected),
                "ndcg_at_10": ndcg_at_k(retrieved, expected, k=10),
                "latency_ms": round(latency_ms, 2),
            })

    return per_config


def _summarize(rows: list[dict]) -> dict:
    return {
        "n": len(rows),
        "hit_rate_at_5": round(mean(r["hit_rate_at_5"] for r in rows), 4),
        "recall_at_5": round(mean(r["recall_at_5"] for r in rows), 4),
        "mrr": round(mean(r["mrr"] for r in rows), 4),
        "ndcg_at_10": round(mean(r["ndcg_at_10"] for r in rows), 4),
        "avg_latency_ms": round(mean(r["latency_ms"] for r in rows), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    examples = json.loads(_DATASET_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(examples)} queries from {_DATASET_PATH}")

    per_config = asyncio.run(_run_all(examples))

    summaries = {}
    print("\n" + "=" * 70)
    print(f"SUMMARY -- {len(examples)} queries, top_k={_TOP_K}")
    print("=" * 70)
    for name, rows in per_config.items():
        summary = _summarize(rows)
        summaries[name] = summary
        print(
            f"{name:20s} hit_rate@5={summary['hit_rate_at_5']:.3f} "
            f"recall@5={summary['recall_at_5']:.3f} mrr={summary['mrr']:.3f} "
            f"ndcg@10={summary['ndcg_at_10']:.3f} avg_latency_ms={summary['avg_latency_ms']:.1f}"
        )

    if args.out:
        with open(args.out, "w") as f:
            json.dump({"summaries": summaries, "per_config": per_config}, f, indent=2)
        print(f"\nFull results written to {args.out}")


if __name__ == "__main__":
    main()
