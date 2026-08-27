from collections.abc import Iterable

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from core.config import settings
from schemas.documents import ChunkRecord
from services.corpus import load_chunk_records


class VectorSearchService:
    def __init__(self) -> None:
        self._model = SentenceTransformer(settings.embed_model)
        self._records = list(load_chunk_records())
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

    def records(self) -> Iterable[ChunkRecord]:
        return self._records
