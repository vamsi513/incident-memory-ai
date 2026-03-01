from sentence_transformers import CrossEncoder

from core.config import settings


class Reranker:
    def __init__(self) -> None:
        self.model = CrossEncoder(settings.rerank_model)

    def rerank(self, query: str, records: list[dict], top_n: int = 5) -> list[dict]:
        pairs = [[query, record["text"]] for record in records]
        scores = self.model.predict(pairs)

        rescored = []
        for record, score in zip(records, scores):
            row = dict(record)
            row["rerank_score"] = float(score)
            rescored.append(row)

        rescored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return rescored[:top_n]

