from schemas.eval import EvalSample, RetrievalEvalReport, RetrievalEvalResult
from schemas.search import SearchRequest
from services.bm25_service import BM25Service
from services.hybrid_search_service import HybridSearchService
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService


async def run_retrieval_eval() -> RetrievalEvalReport:
    service = HybridSearchService(
        bm25_service=BM25Service(),
        vector_service=VectorSearchService(),
        rerank_service=RerankService(),
        parent_retrieval_service=ParentRetrievalService(),
    )
    samples = [
        EvalSample(
            question="What was the root cause of the search latency incident?",
            expected_parent_ids=["incident_2025_02_search_latency"],
        ),
        EvalSample(
            question="What fixed the checkout timeout incident?",
            expected_parent_ids=["incident_2025_01_checkout_timeout"],
        ),
        EvalSample(
            question="What runbook steps help with database latency?",
            expected_parent_ids=["database_latency_runbook"],
        ),
    ]

    results: list[RetrievalEvalResult] = []
    for sample in samples:
        response = await service.search(SearchRequest(query=sample.question))
        matched = [result.parent_id for result in response.results if result.parent_id in sample.expected_parent_ids]
        hit_rate = 1.0 if matched else 0.0
        results.append(
            RetrievalEvalResult(
                question=sample.question,
                hit_rate=hit_rate,
                matched_parent_ids=matched,
            )
        )

    average_hit_rate = sum(result.hit_rate for result in results) / len(results)
    return RetrievalEvalReport(
        total_samples=len(results),
        average_hit_rate=average_hit_rate,
        results=results,
    )


if __name__ == "__main__":
    import asyncio
    import json

    report = asyncio.run(run_retrieval_eval())
    print(json.dumps(report.model_dump(), indent=2))
