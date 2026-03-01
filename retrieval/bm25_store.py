import re

from rank_bm25 import BM25Okapi


TOKEN_RE = re.compile(r"\b\w+\b")


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Store:
    def __init__(self, texts: list[str], records: list[dict]) -> None:
        self.records = records
        self.tokens = [_tokenize(text) for text in texts]
        self.bm25 = BM25Okapi(self.tokens)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_tokens = _tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        results = []
        for idx, score in ranked:
            row = dict(self.records[idx])
            row["bm25_score"] = float(score)
            results.append(row)

        return results
