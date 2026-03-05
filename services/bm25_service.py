import re
from collections.abc import Iterable

from rank_bm25 import BM25Okapi

from schemas.documents import ChunkMetadata, ChunkRecord


class BM25Service:
    def __init__(self) -> None:
        self._records = self._bootstrap_records()
        self._tokenized_corpus = [self._tokenize(record.text) for record in self._records]
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    async def search(self, query: str, top_k: int = 10) -> list[ChunkRecord]:
        scores = self._bm25.get_scores(self._tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda row: row[1], reverse=True)[:top_k]
        results: list[ChunkRecord] = []
        for idx, score in ranked:
            record = self._records[idx].model_copy(deep=True)
            record.score = float(score)
            results.append(record)
        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9_]+", text.lower())

    @staticmethod
    def _bootstrap_records() -> list[ChunkRecord]:
        return [
            ChunkRecord(
                chunk_id="chunk-checkout-root-cause",
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
                chunk_id="chunk-checkout-mitigation",
                document_id="incident_2025_01_checkout_timeout",
                text="The incident was mitigated by rolling back the deployment and increasing the connection pool size.",
                metadata=ChunkMetadata(
                    source="incident_postmortem",
                    parent_id="incident_2025_01_checkout_timeout",
                    section="Mitigation",
                    service="checkout",
                ),
            ),
            ChunkRecord(
                chunk_id="chunk-search-root-cause",
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
                chunk_id="chunk-runbook-checks",
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
