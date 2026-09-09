"""
scripts/measure_latency.py — Real P50/P90/P95/P99 retrieval latency on the
current 60-query eval set, against the actual production HybridSearchService
(same path api/main.py's /v1/search uses).

Usage:
    python -m scripts.measure_latency
    python -m scripts.measure_latency --repeats 3
"""

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

from schemas.search import SearchRequest
from services.bm25_service import BM25Service
from services.hybrid_search_service import HybridSearchService
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService

_DATASET_PATH = Path("evals/dataset.json")


def _percentile(sorted_values: list[float], p: float) -> float:
    n = len(sorted_values)
    idx = min(n - 1, int(round(p / 100 * n)))
    return sorted_values[idx]


async def _run(repeats: int) -> list[float]:
    examples = json.loads(_DATASET_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(examples)} queries from {_DATASET_PATH}")

    service = HybridSearchService(
        bm25_service=BM25Service(),
        vector_service=VectorSearchService(),
        rerank_service=RerankService(),
        parent_retrieval_service=ParentRetrievalService(),
    )

    latencies: list[float] = []
    for rep in range(repeats):
        for example in examples:
            t0 = time.perf_counter()
            await service.search(SearchRequest(query=example["query"], top_k=5))
            latencies.append((time.perf_counter() - t0) * 1000)
        print(f"Repeat {rep + 1}/{repeats} done ({len(examples)} queries)")

    return latencies


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=1,
                         help="Run the full query set this many times (default 1; more repeats stabilize the tail percentiles).")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    latencies = asyncio.run(_run(args.repeats))
    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)

    result = {
        "n_measurements": n,
        "n_queries": n // args.repeats,
        "repeats": args.repeats,
        "min_ms": round(min(latencies_sorted), 2),
        "max_ms": round(max(latencies_sorted), 2),
        "mean_ms": round(statistics.mean(latencies_sorted), 2),
        "p50_ms": round(_percentile(latencies_sorted, 50), 2),
        "p90_ms": round(_percentile(latencies_sorted, 90), 2),
        "p95_ms": round(_percentile(latencies_sorted, 95), 2),
        "p99_ms": round(_percentile(latencies_sorted, 99), 2),
    }

    print("\n" + "=" * 60)
    print(f"RETRIEVAL LATENCY -- {n} real measurements ({result['n_queries']} queries x {args.repeats} repeat(s))")
    print("=" * 60)
    for k, v in result.items():
        print(f"{k}: {v}")

    if args.out:
        with open(args.out, "w") as f:
            json.dump({"summary": result, "raw_latencies_ms": [round(x, 2) for x in latencies]}, f, indent=2)
        print(f"\nFull results written to {args.out}")


if __name__ == "__main__":
    main()
