import json
from pathlib import Path

from schemas.documents import ChunkRecord
from schemas.search import SearchResult

_SECTION_ORDER = [
    "summary", "impact", "root cause", "mitigation",
    "mitigation steps", "immediate checks", "follow-up actions",
    "escalation", "symptoms", "overview", "services",
    "failure modes", "mitigations", "circuit breaker", "rate limiting",
]

_INDEX_PATH = Path("data/processed/index_records.json")


def _build_parent_index() -> dict[str, dict]:
    if not _INDEX_PATH.exists():
        return {}

    records = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))

    grouped: dict[str, list[dict]] = {}
    for record in records:
        pid = record.get("parent_id") or record.get("doc_id", "")
        grouped.setdefault(pid, []).append(record)

    parents: dict[str, dict] = {}
    for pid, chunks in grouped.items():
        title = chunks[0].get("title", pid) if chunks else pid

        def section_rank(chunk: dict) -> int:
            section = (chunk.get("section") or "").strip().lower()
            try:
                return _SECTION_ORDER.index(section)
            except ValueError:
                return len(_SECTION_ORDER)

        sorted_chunks = sorted(chunks, key=section_rank)

        parts: list[str] = []
        char_budget = 600
        for chunk in sorted_chunks:
            section = (chunk.get("section") or "").strip()
            text = (chunk.get("text") or "").strip()
            if not text:
                continue
            fragment = f"{section}: {text}" if section else text
            if len(fragment) > char_budget:
                fragment = fragment[:char_budget]
            parts.append(fragment)
            char_budget -= len(fragment)
            if char_budget <= 0:
                break

        parents[pid] = {
            "title": title,
            "body": " ".join(parts),
        }

    return parents


class ParentRetrievalService:
    def __init__(self) -> None:
        self._parents = _build_parent_index()

    async def assemble(self, chunks: list[ChunkRecord]) -> list[SearchResult]:
        grouped: dict[str, list[ChunkRecord]] = {}
        for chunk in chunks:
            grouped.setdefault(chunk.metadata.parent_id, []).append(chunk)

        results: list[SearchResult] = []
        for parent_id, supporting_chunks in grouped.items():
            parent = self._parents.get(parent_id, {"title": parent_id, "body": ""})
            supporting_chunks.sort(key=lambda row: row.score, reverse=True)
            results.append(
                SearchResult(
                    parent_id=parent_id,
                    title=parent["title"],
                    summary=parent["body"],
                    final_score=supporting_chunks[0].score,
                    supporting_chunks=supporting_chunks,
                    metadata={"source": supporting_chunks[0].metadata.source},
                )
            )

        results.sort(key=lambda row: row.final_score, reverse=True)
        return results
