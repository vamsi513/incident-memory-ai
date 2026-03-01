from pathlib import Path
from ingestion.models import RawDocument


def load_markdown_files(base_dir: str) -> list[RawDocument]:
    docs = []

    for path in Path(base_dir).rglob("*.md"):
        docs.append(
            RawDocument(
                doc_id=path.stem,
                source="local_markdown",
                title=path.stem.replace("_", " ").title(),
                content=path.read_text(encoding="utf-8"),
                path=str(path),
                metadata={"file_type": "md"},
            )
        )

    return docs

