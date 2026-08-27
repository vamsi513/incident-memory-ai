import pytest

from schemas.search import SearchRequest
from services.bm25_service import BM25Service
from services.hybrid_search_service import HybridSearchService
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService


@pytest.mark.asyncio
async def test_hybrid_search_prefers_checkout_parent_document_for_fix_queries():
    service = HybridSearchService(
        bm25_service=BM25Service(),
        vector_service=VectorSearchService(),
        rerank_service=RerankService(),
        parent_retrieval_service=ParentRetrievalService(),
    )

    response = await service.search(
        SearchRequest(query="What fixed the checkout timeout incident?", top_k=3)
    )

    result_ids = [r.parent_id for r in response.results]
    assert "incident_2025_01_checkout_timeout" in result_ids

    checkout_result = next(
        r for r in response.results if r.parent_id == "incident_2025_01_checkout_timeout"
    )
    assert "connection pool" in checkout_result.summary.lower()
