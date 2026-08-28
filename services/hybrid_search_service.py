import math

from core.config import settings
from core.exceptions import ProviderError, RetrievalError
from core.tracing import traced_span
from schemas.documents import ChunkRecord
from schemas.search import SearchFilters, SearchRequest, SearchResponse, SearchResult
from services.bm25_service import BM25Service
from services.corpus import load_chunk_records
from services.parent_retrieval_service import ParentRetrievalService
from services.query_rewrite import rewrite_query
from services.rerank_service import RerankService
from services.vector_service import VectorSearchService

# final_score is a raw, unbounded cross-encoder logit. Below this
# sigmoid-normalized relevance, a result is noise rather than a genuine
# match (e.g. querying for an incident type the corpus doesn't contain)
# and showing it would mislead the user more than an empty result would.
# Calibrated against real query logits: genuine matches on hard paraphrases
# score around -7.5 to -8 (sigmoid ~0.0003-0.0005), while true corpus
# misses (e.g. an SSL-certificate query with no matching incident) score
# around -10.6 to -11.2 (sigmoid ~0.00002-0.00004). 0.0001 sits in the
# gap between them.
_MIN_RELEVANCE = 0.0001

# Rerank a wider candidate pool than the requested top_k so section
# boosting has real headroom to reorder results before final truncation.
_RERANK_CANDIDATE_WINDOW = 12

# Chunks whose service/doc_id doesn't overlap one of these terms with the
# query are excluded from section-based candidate injection below.
_SERVICE_TERMS = {"checkout", "search", "database", "latency", "timeout"}


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
                with traced_span("hybrid_search.retrieve"):
                    result_sets: list[list[ChunkRecord]] = []
                    for rewritten_query in rewrite_query(payload.query):
                        result_sets.append(
                            await self.bm25_service.search(rewritten_query, top_k=settings.top_k)
                        )
                        result_sets.append(
                            await self.vector_service.search(rewritten_query, top_k=settings.top_k)
                        )

                fused_hits = self._fuse_hits(result_sets)
                candidates = self._dedupe(fused_hits + self._inject_section_candidates(payload.query))
                candidates = self._apply_filters(candidates, payload.filters)

                rerank_window = max(payload.top_k, _RERANK_CANDIDATE_WINDOW)
                # Score every candidate before truncating: boosting needs the
                # full scored pool to have a chance at promoting an injected
                # chunk the cross-encoder alone ranked below the window.
                with traced_span("hybrid_search.rerank"):
                    reranked_hits = await self.rerank_service.rerank(
                        payload.query, candidates, top_n=len(candidates)
                    )
                reranked_hits = self._apply_section_boosts(reranked_hits, payload.query)[:rerank_window]

                with traced_span("hybrid_search.parent_assembly"):
                    parent_results = await self.parent_retrieval_service.assemble(reranked_hits)
                parent_results = self._drop_irrelevant(parent_results)
                return SearchResponse(query=payload.query, results=parent_results[: payload.top_k])
        except ProviderError:
            raise
        except Exception as exc:  # pragma: no cover - safety boundary
            raise RetrievalError(str(exc)) from exc

    @staticmethod
    def _dedupe(hits: list[ChunkRecord]) -> list[ChunkRecord]:
        seen: set[str] = set()
        deduped: list[ChunkRecord] = []
        for hit in hits:
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            deduped.append(hit)
        return deduped

    @staticmethod
    def _inject_section_candidates(query: str) -> list[ChunkRecord]:
        query_lower = query.lower()
        sections_to_prioritize: set[str] = set()

        if "root cause" in query_lower:
            sections_to_prioritize.add("root cause")
        if any(term in query_lower for term in ["fixed", "resolve", "resolved", "mitigation"]):
            sections_to_prioritize.update({"mitigation", "mitigation steps"})
        if any(term in query_lower for term in ["runbook", "steps", "checks"]):
            sections_to_prioritize.update({"immediate checks", "mitigation steps", "escalation"})

        if not sections_to_prioritize:
            return []

        query_terms = {term for term in _SERVICE_TERMS if term in query_lower}

        injected: list[ChunkRecord] = []
        for record in load_chunk_records():
            section = (record.metadata.section or "").strip().lower()
            if section not in sections_to_prioritize:
                continue

            haystack = " ".join(
                [record.document_id, record.text, record.metadata.service or ""]
            ).lower()
            if query_terms and not any(term in haystack for term in query_terms):
                continue

            injected.append(record)

        return injected

    @staticmethod
    def _apply_section_boosts(hits: list[ChunkRecord], query: str) -> list[ChunkRecord]:
        query_lower = query.lower()
        asks_for_resolution = any(
            term in query_lower for term in ["fixed", "resolve", "resolved", "mitigation"]
        )
        asks_for_runbook_steps = any(
            term in query_lower for term in ["runbook", "steps", "checks"]
        )

        boosted: list[ChunkRecord] = []
        for hit in hits:
            item = hit.model_copy(deep=True)
            section = (item.metadata.section or "").strip().lower()
            boost = 0.0

            if "root cause" in query_lower and section == "root cause":
                boost += 3.0
            elif "root cause" in query_lower and section in {"summary", "impact"}:
                boost -= 1.0

            if asks_for_resolution and section in {"mitigation", "mitigation steps"}:
                boost += 6.0
            elif asks_for_resolution and section in {"summary", "impact"}:
                boost -= 2.0
            elif asks_for_resolution and section == "root cause":
                boost += 0.5

            if asks_for_runbook_steps and section in {
                "immediate checks", "mitigation steps", "escalation",
            }:
                boost += 2.0
            elif asks_for_runbook_steps and section == "symptoms":
                boost -= 0.5

            item.score = hit.score + boost
            boosted.append(item)

        return sorted(boosted, key=lambda row: row.score, reverse=True)

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
    def _fuse_hits(result_sets: list[list[ChunkRecord]]) -> list[ChunkRecord]:
        rrf_scores: dict[str, float] = {}
        records: dict[str, ChunkRecord] = {}

        for result_set in result_sets:
            for rank, hit in enumerate(result_set, start=1):
                rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + 1.0 / (60 + rank)
                records.setdefault(hit.chunk_id, hit)

        fused: list[ChunkRecord] = []
        for chunk_id, score in rrf_scores.items():
            item = records[chunk_id].model_copy(deep=True)
            item.score = score
            fused.append(item)

        return sorted(fused, key=lambda row: row.score, reverse=True)
