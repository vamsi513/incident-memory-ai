from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "incidentmemory-enterprise-rag"
    app_env: str = "dev"
    log_level: str = "INFO"
    api_port: int = 8000
    postgres_dsn: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/incidentmemory"
    )
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "incident_chunks"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    langsmith_api_key: str = ""
    top_k: int = 10
    rerank_top_n: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
