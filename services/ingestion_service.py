from pathlib import Path

from schemas.documents import ParentDocument


class IngestionService:
    async def ingest_directory(self, base_path: str) -> list[ParentDocument]:
        documents: list[ParentDocument] = []
        for path in Path(base_path).rglob("*.md"):
            documents.append(
                ParentDocument(
                    parent_id=path.stem,
                    title=path.stem.replace("_", " ").title(),
                    body=path.read_text(encoding="utf-8"),
                    source=str(path),
                )
            )
        return documents
