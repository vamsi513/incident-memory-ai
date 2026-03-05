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

    assert response.results[0].parent_id == "incident_2025_01_checkout_timeout"
    supporting_sections = {
        chunk["metadata"]["section"] if isinstance(chunk, dict) else chunk.metadata.section
        for chunk in response.results[0].supporting_chunks
    }
    assert "Mitigation" in supporting_sections
