from collections.abc import Iterable

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from core.config import settings
from schemas.documents import ChunkMetadata, ChunkRecord


class VectorSearchService:
    def __init__(self) -> None:
        self._model = SentenceTransformer(settings.embed_model)
        self._records = self._bootstrap_records()
        self._index = self._build_index()

    def _build_index(self) -> faiss.IndexFlatIP:
        texts = [r.text for r in self._records]
        embeddings = self._model.encode(texts, normalize_embeddings=True).astype(np.float32)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        return index

    async def search(self, query: str, top_k: int = 10) -> list[ChunkRecord]:
        query_vec = self._model.encode([query], normalize_embeddings=True).astype(np.float32)
        k = min(top_k, len(self._records))
        scores, indices = self._index.search(query_vec, k)
        results: list[ChunkRecord] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            record = self._records[idx].model_copy(deep=True)
            record.score = float(score)
            results.append(record)
        return results

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
