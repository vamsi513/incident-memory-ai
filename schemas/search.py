from typing import Any

from pydantic import BaseModel, Field

from schemas.documents import ChunkRecord


class SearchFilters(BaseModel):
    service: str | None = None
    severity: str | None = None
    source: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: SearchFilters | None = None


class SearchResult(BaseModel):
    parent_id: str
    title: str
    summary: str
    final_score: float
    supporting_chunks: list[ChunkRecord]
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
