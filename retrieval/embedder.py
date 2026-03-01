from sentence_transformers import SentenceTransformer

from core.config import settings


class Embedder:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embed_model)

    def encode(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(
            texts,
            normalize_embeddings=True,
        ).tolist()

