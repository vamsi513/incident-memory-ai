from pydantic import BaseModel, Field
from typing import Any


class RawDocument(BaseModel):
    doc_id: str
    source: str
    title: str
    content: str
    url: str | None = None
    path: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

