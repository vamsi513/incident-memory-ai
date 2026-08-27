import math

from core.config import settings
from core.exceptions import ProviderError, RetrievalError
from core.tracing import traced_span
from schemas.documents import ChunkRecord
from schemas.search import SearchFilters, SearchRequest, SearchResponse, SearchResult
from services.bm25_service import BM25Service
from services.parent_retrieval_service import ParentRetrievalService
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService

# final_score is a raw, unbounded cross-encoder logit. Below this
# sigmoid-normalized relevance, a result is noise rather than a genuine
# match (e.g. querying for an incident type the corpus doesn't contain)
# and showing it would mislead the user more than an empty result would.
_MIN_RELEVANCE = 0.01


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
                fused_hits = self._apply_filters(fused_hits, payload.filters)
                reranked_hits = await self.rerank_service.rerank(
                    payload.query, fused_hits, top_n=payload.top_k
                )
                parent_results = await self.parent_retrieval_service.assemble(reranked_hits)
                parent_results = self._drop_irrelevant(parent_results)
                return SearchResponse(query=payload.query, results=parent_results[: payload.top_k])
        except ProviderError:
            raise
        except Exception as exc:  # pragma: no cover - safety boundary
            raise RetrievalError(str(exc)) from exc

    @staticmethod
    def _drop_irrelevant(results: list[SearchResult]) -> list[SearchResult]:
        def normalized(result: SearchResult) -> float:
            return 1.0 / (1.0 + math.exp(-result.final_score))

        return [r for r in results if normalized(r) >= _MIN_RELEVANCE]

    @staticmethod
    def _apply_filters(hits: list[ChunkRecord], filters: SearchFilters | None) -> list[ChunkRecord]:
        if filters is None:
            return hits

        def matches(hit: ChunkRecord) -> bool:
            if filters.service and hit.metadata.service != filters.service:
                return False
            if filters.severity and hit.metadata.severity != filters.severity:
                return False
            if filters.source and hit.metadata.source != filters.source:
                return False
            return True

        return [hit for hit in hits if matches(hit)]

    @staticmethod
    def _fuse_hits(bm25_hits: list[ChunkRecord], vector_hits: list[ChunkRecord]) -> list[ChunkRecord]:
        rrf_scores: dict[str, float] = {}
        records: dict[str, ChunkRecord] = {}

        for rank, hit in enumerate(bm25_hits, start=1):
            rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + 1.0 / (60 + rank)
            records[hit.chunk_id] = hit

        for rank, hit in enumerate(vector_hits, start=1):
            rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + 1.0 / (60 + rank)
            records.setdefault(hit.chunk_id, hit)

        fused: list[ChunkRecord] = []
        for chunk_id, score in rrf_scores.items():
            item = records[chunk_id].model_copy(deep=True)
            item.score = score
            fused.append(item)

        return sorted(fused, key=lambda row: row.score, reverse=True)
