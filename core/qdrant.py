from functools import lru_cache

from qdrant_client import AsyncQdrantClient

from core.config import settings


class QdrantClientSingleton:
    _client: AsyncQdrantClient | None = None

    @classmethod
    def get_client(cls) -> AsyncQdrantClient:
        if cls._client is None:
            cls._client = AsyncQdrantClient(url=settings.qdrant_url)
        return cls._client


@lru_cache(maxsize=1)
def get_qdrant_client() -> AsyncQdrantClient:
    return QdrantClientSingleton.get_client()
