import re
from collections.abc import Iterable

from rank_bm25 import BM25Okapi

from schemas.documents import ChunkRecord
from services.corpus import load_chunk_records


class BM25Service:
    def __init__(self) -> None:
        self._records = list(load_chunk_records())
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

    def records(self) -> Iterable[ChunkRecord]:
        return self._records
