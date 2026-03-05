from schemas.documents import ChunkRecord
from schemas.search import SearchResult


class ParentRetrievalService:
    def __init__(self) -> None:
        self._parents = {
            "incident_2025_01_checkout_timeout": {
                "title": "Checkout Timeout Incident",
                "body": (
                    "Summary: Elevated checkout timeout errors. "
                    "Root Cause: deployment changed connection pool behavior. "
                    "Mitigation: rollback plus pool increase."
                ),
            },
            "incident_2025_02_search_latency": {
                "title": "Search Latency Incident",
                "body": (
                    "Summary: Search latency spiked. "
                    "Root Cause: cache invalidation bug. "
                    "Mitigation: disabled invalidation worker and restored warmup."
                ),
            },
            "database_latency_runbook": {
                "title": "Database Latency Runbook",
                "body": (
                    "Immediate Checks: database CPU, active connections, recent deploys. "
                    "Escalation: contact DB owner if saturation persists."
                ),
            },
        }

    async def assemble(self, chunks: list[ChunkRecord]) -> list[SearchResult]:
        grouped: dict[str, list[ChunkRecord]] = {}
        for chunk in chunks:
            grouped.setdefault(chunk.metadata.parent_id, []).append(chunk)

        results: list[SearchResult] = []
        for parent_id, supporting_chunks in grouped.items():
            parent = self._parents.get(parent_id, {"title": parent_id, "body": ""})
            supporting_chunks.sort(key=lambda row: row.score, reverse=True)
            results.append(
                SearchResult(
                    parent_id=parent_id,
                    title=parent["title"],
                    summary=parent["body"],
                    final_score=supporting_chunks[0].score,
                    supporting_chunks=supporting_chunks,
                    metadata={"source": supporting_chunks[0].metadata.source},
                )
            )
        results.sort(key=lambda row: row.final_score, reverse=True)
        return results
