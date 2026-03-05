from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    source: str
    parent_id: str
    section: str | None = None
    service: str | None = None
    created_at: datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float = 0.0
    metadata: ChunkMetadata


class ParentDocument(BaseModel):
    parent_id: str
    title: str
    body: str
    source: str
