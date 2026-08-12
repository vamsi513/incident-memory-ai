"""
services/qdrant_service.py — Qdrant-backed vector search for IncidentMemory.

Replaces the hardcoded VectorSearchService stub with a real Qdrant collection
so the index persists across restarts and scales to production volumes.
The async QdrantClient from core/qdrant.py is reused here.

Configuration (environment variables):
    QDRANT_URL        — Qdrant server URL (default: http://localhost:6333)
    QDRANT_COLLECTION — Collection name (default: incident_memory)
"""

import logging
import os
import uuid
from collections.abc import Iterable

from core.config import settings
from core.qdrant import get_qdrant_client
from schemas.documents import ChunkMetadata, ChunkRecord

logger = logging.getLogger(__name__)

_COLLECTION = os.getenv("QDRANT_COLLECTION", "incident_memory")
_DIMENSION = 384   # all-MiniLM-L6-v2 output dimension; update if model changes

try:
    from qdrant_client.http.models import (
        Distance,
        PointStruct,
        VectorParams,
    )
    from sentence_transformers import SentenceTransformer
    _DEPS_AVAILABLE = True
except ImportError:
    _DEPS_AVAILABLE = False
    logger.warning("qdrant-client or sentence-transformers not installed")


class QdrantSearchService:
    """
    Async vector search service backed by Qdrant.

    Drop-in replacement for VectorSearchService — same async interface so
    HybridSearchService requires no changes.
    """

    def __init__(self) -> None:
        if not _DEPS_AVAILABLE:
            raise RuntimeError("Install qdrant-client and sentence-transformers")

        self._model = SentenceTransformer(settings.embed_model)
        self._client = get_qdrant_client()

    async def _ensure_collection(self) -> None:
        existing = await self._client.get_collections()
        names = [c.name for c in existing.collections]
        if _COLLECTION not in names:
            await self._client.create_collection(
                collection_name=_COLLECTION,
                vectors_config=VectorParams(
                    size=self._model.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection '%s'", _COLLECTION)

    async def search(self, query: str, top_k: int = 10) -> list[ChunkRecord]:
        await self._ensure_collection()

        query_emb = self._model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        )[0].tolist()

        hits = await self._client.search(
            collection_name=_COLLECTION,
            query_vector=query_emb,
            limit=top_k,
            with_payload=True,
        )

        results: list[ChunkRecord] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                ChunkRecord(
                    chunk_id=payload.get("chunk_id", str(hit.id)),
                    document_id=payload.get("document_id", ""),
                    text=payload.get("text", ""),
                    score=float(hit.score),
                    metadata=ChunkMetadata(
                        source=payload.get("source", ""),
                        parent_id=payload.get("parent_id", ""),
                        section=payload.get("section"),
                        service=payload.get("service"),
                    ),
                )
            )

        logger.debug(
            "Qdrant: %d results for query '%.60s'", len(results), query
        )
        return results

    async def add_chunks(self, chunks: list[ChunkRecord]) -> None:
        if not chunks:
            return

        await self._ensure_collection()

        embeddings = self._model.encode(
            [c.text for c in chunks],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "source": chunk.metadata.source,
                    "parent_id": chunk.metadata.parent_id,
                    "section": chunk.metadata.section,
                    "service": chunk.metadata.service,
                },
            )
            for chunk, emb in zip(chunks, embeddings)
        ]

        await self._client.upsert(collection_name=_COLLECTION, points=points)
        logger.info("Upserted %d chunks into Qdrant '%s'", len(points), _COLLECTION)

    async def count(self) -> int:
        await self._ensure_collection()
        info = await self._client.get_collection(_COLLECTION)
        return info.points_count or 0

    def records(self) -> Iterable[ChunkRecord]:
        raise NotImplementedError(
            "Use async add_chunks/search. Sync records() not supported in Qdrant service."
        )
