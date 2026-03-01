import json
from pathlib import Path

import faiss
import numpy as np


class FaissStore:
    def __init__(self, dim: int) -> None:
        self.index = faiss.IndexFlatIP(dim)
        self.records: list[dict] = []

    def add(self, embeddings: list[list[float]], records: list[dict]) -> None:
        arr = np.array(embeddings, dtype="float32")
        self.index.add(arr)
        self.records.extend(records)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        arr = np.array([query_embedding], dtype="float32")
        scores, indices = self.index.search(arr, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            row = dict(self.records[idx])
            row["vector_score"] = float(score)
            results.append(row)

        return results

    def save(self, output_dir: str) -> None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(out / "index.faiss"))
        (out / "index_records.json").write_text(
            json.dumps(self.records, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, output_dir: str) -> "FaissStore":
        out = Path(output_dir)
        index = faiss.read_index(str(out / "index.faiss"))
        records = json.loads((out / "index_records.json").read_text(encoding="utf-8"))

        store = cls(dim=index.d)
        store.index = index
        store.records = records
        return store

