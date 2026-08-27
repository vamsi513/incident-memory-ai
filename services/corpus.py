import json
from functools import lru_cache
from pathlib import Path

from schemas.documents import ChunkMetadata, ChunkRecord

_CHUNKS_PATH = Path("data/processed/chunks.json")

_SOURCE_BY_DIR = {
    "incidents": "incident_postmortem",
    "runbooks": "runbook",
    "docs": "architecture_doc",
}


def _source_for(chunk: dict) -> str:
    path = chunk.get("path") or ""
    parts = Path(path).parts
    for part in parts:
        if part in _SOURCE_BY_DIR:
            return _SOURCE_BY_DIR[part]
    return chunk.get("source", "unknown")


@lru_cache(maxsize=1)
def load_chunk_records() -> tuple[ChunkRecord, ...]:
    raw = json.loads(_CHUNKS_PATH.read_text(encoding="utf-8"))
    records = []
    for chunk in raw:
        records.append(
            ChunkRecord(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["doc_id"],
                text=chunk["text"],
                metadata=ChunkMetadata(
                    source=_source_for(chunk),
                    parent_id=chunk.get("parent_id") or chunk["doc_id"],
                    section=chunk.get("section"),
                    service=chunk.get("service"),
                    severity=chunk.get("severity"),
                ),
            )
        )
    return tuple(records)
