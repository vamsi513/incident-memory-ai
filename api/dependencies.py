from functools import lru_cache

from core.llm_factory import LLMProviderFactory
from services.bm25_service import BM25Service
from services.hybrid_search_service import HybridSearchService
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService


@lru_cache(maxsize=1)
def get_bm25_service() -> BM25Service:
    return BM25Service()


@lru_cache(maxsize=1)
def get_vector_service() -> VectorSearchService:
    return VectorSearchService()


@lru_cache(maxsize=1)
def get_rerank_service() -> RerankService:
    return RerankService()


@lru_cache(maxsize=1)
def get_parent_retrieval_service() -> ParentRetrievalService:
    return ParentRetrievalService()


@lru_cache(maxsize=1)
def get_hybrid_search_service() -> HybridSearchService:
    return HybridSearchService(
        bm25_service=get_bm25_service(),
        vector_service=get_vector_service(),
        rerank_service=get_rerank_service(),
        parent_retrieval_service=get_parent_retrieval_service(),
    )


@lru_cache(maxsize=1)
def get_judge_provider_factory() -> LLMProviderFactory:
    return LLMProviderFactory()
