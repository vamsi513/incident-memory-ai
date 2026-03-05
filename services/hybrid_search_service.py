from core.config import settings
from core.exceptions import ProviderError, RetrievalError
from core.tracing import traced_span
from schemas.documents import ChunkRecord
from schemas.search import SearchRequest, SearchResponse
from services.bm25_service import BM25Service
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService


class HybridSearchService:
    def __init__(
        self,
        bm25_service: BM25Service,
        vector_service: VectorSearchService,
        rerank_service: RerankService,
        parent_retrieval_service: ParentRetrievalService,
    ) -> None:
        self.bm25_service = bm25_service
        self.vector_service = vector_service
        self.rerank_service = rerank_service
        self.parent_retrieval_service = parent_retrieval_service

    async def search(self, payload: SearchRequest) -> SearchResponse:
        try:
            with traced_span("hybrid_search"):
                bm25_hits = await self.bm25_service.search(payload.query, top_k=settings.top_k)
                vector_hits = await self.vector_service.search(payload.query, top_k=settings.top_k)
                fused_hits = self._fuse_hits(bm25_hits, vector_hits)
                reranked_hits = await self.rerank_service.rerank(
                    payload.query, fused_hits, top_n=payload.top_k
                )
                parent_results = await self.parent_retrieval_service.assemble(reranked_hits)
                return SearchResponse(query=payload.query, results=parent_results[: payload.top_k])
        except ProviderError:
            raise
        except Exception as exc:  # pragma: no cover - safety boundary
            raise RetrievalError(str(exc)) from exc

    @staticmethod
    def _fuse_hits(bm25_hits: list[ChunkRecord], vector_hits: list[ChunkRecord]) -> list[ChunkRecord]:
        fused: dict[str, ChunkRecord] = {}
        for rank, hit in enumerate(bm25_hits, start=1):
            item = hit.model_copy(deep=True)
            item.score = 1.0 / (60 + rank)
            fused[item.chunk_id] = item

        for rank, hit in enumerate(vector_hits, start=1):
            item = hit.model_copy(deep=True)
            item.score = fused.get(item.chunk_id, item).score + (1.0 / (60 + rank))
            fused[item.chunk_id] = item

        return sorted(fused.values(), key=lambda row: row.score, reverse=True)
