from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    github_token: str = ""
    app_env: str = "dev"
    log_level: str = "INFO"
    data_dir: str = "./data"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: int = 8
    rerank_top_n: int = 5
    max_chunk_tokens: int = 350
    chunk_overlap_tokens: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

