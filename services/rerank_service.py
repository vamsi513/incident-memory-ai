from sentence_transformers import CrossEncoder

from core.config import settings
from schemas.documents import ChunkRecord


class RerankService:
    def __init__(self) -> None:
        self._model = CrossEncoder(settings.rerank_model)

    async def rerank(self, query: str, candidates: list[ChunkRecord], top_n: int) -> list[ChunkRecord]:
        if not candidates:
            return []
        pairs = [[query, c.text] for c in candidates]
        scores = self._model.predict(pairs)
        rescored: list[ChunkRecord] = []
        for candidate, score in zip(candidates, scores):
            item = candidate.model_copy(deep=True)
            item.score = float(score)
            rescored.append(item)
        rescored.sort(key=lambda row: row.score, reverse=True)
        return rescored[:top_n]
