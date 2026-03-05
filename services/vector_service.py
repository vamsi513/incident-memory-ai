from collections.abc import Iterable

from schemas.documents import ChunkMetadata, ChunkRecord


class VectorSearchService:
    def __init__(self) -> None:
        self._records = self._bootstrap_records()

    async def search(self, query: str, top_k: int = 10) -> list[ChunkRecord]:
        query_lower = query.lower()
        ranked: list[tuple[float, ChunkRecord]] = []
        for record in self._records:
            score = self._semantic_overlap(query_lower, record.text.lower(), record.metadata.section)
            ranked.append((score, record))
        ranked.sort(key=lambda row: row[0], reverse=True)
        results: list[ChunkRecord] = []
        for score, record in ranked[:top_k]:
            item = record.model_copy(deep=True)
            item.score = score
            results.append(item)
        return results

    @staticmethod
    def _semantic_overlap(query: str, text: str, section: str | None) -> float:
        score = 0.1
        if "root cause" in query and "causing" in text:
            score += 0.8
        if "fixed" in query and "mitigated" in text:
            score += 0.8
        if "runbook" in query and "check" in text:
            score += 0.8
        if section:
            normalized_section = section.lower()
            if normalized_section in query:
                score += 0.5
        shared_terms = sum(1 for token in query.split() if token in text)
        score += shared_terms * 0.05
        return score

    @staticmethod
    def _bootstrap_records() -> list[ChunkRecord]:
        return [
            ChunkRecord(
                chunk_id="vec-checkout-root-cause",
                document_id="incident_2025_01_checkout_timeout",
                text="A deployment changed database connection pool behavior, causing saturation.",
                metadata=ChunkMetadata(
                    source="incident_postmortem",
                    parent_id="incident_2025_01_checkout_timeout",
                    section="Root Cause",
                    service="checkout",
                ),
            ),
            ChunkRecord(
                chunk_id="vec-checkout-mitigation",
                document_id="incident_2025_01_checkout_timeout",
                text="Rollback of the deployment and increased connection pool size resolved the incident.",
                metadata=ChunkMetadata(
                    source="incident_postmortem",
                    parent_id="incident_2025_01_checkout_timeout",
                    section="Mitigation",
                    service="checkout",
                ),
            ),
            ChunkRecord(
                chunk_id="vec-search-root-cause",
                document_id="incident_2025_02_search_latency",
                text="A cache invalidation bug cleared hot keys too aggressively and spiked search latency.",
                metadata=ChunkMetadata(
                    source="incident_postmortem",
                    parent_id="incident_2025_02_search_latency",
                    section="Root Cause",
                    service="search",
                ),
            ),
            ChunkRecord(
                chunk_id="vec-runbook-checks",
                document_id="database_latency_runbook",
                text="Check database CPU, inspect active connections, and review recent deploys.",
                metadata=ChunkMetadata(
                    source="runbook",
                    parent_id="database_latency_runbook",
                    section="Immediate Checks",
                    service="database",
                ),
            ),
        ]

    def records(self) -> Iterable[ChunkRecord]:
        return self._records
