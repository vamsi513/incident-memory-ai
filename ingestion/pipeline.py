import json
from pathlib import Path

from ingestion.chunker import chunk_section, split_markdown_sections
from ingestion.connectors.local_files import load_markdown_files


def infer_metadata(doc) -> dict:
    path_lower = (doc.path or "").lower()
    title_lower = doc.title.lower()
    content_lower = doc.content.lower()

    service = None
    severity = None
    tags: list[str] = []

    if "checkout" in path_lower or "checkout" in title_lower or "checkout" in content_lower:
        service = "checkout"
        tags.append("checkout")

    if "search" in path_lower or "search" in title_lower or "search" in content_lower:
        service = "search"
        tags.append("search")

    if "database" in path_lower or "database" in title_lower or "database" in content_lower:
        tags.append("database")

    if "latency" in path_lower or "latency" in title_lower or "latency" in content_lower:
        tags.append("latency")

    if "timeout" in path_lower or "timeout" in title_lower or "timeout" in content_lower:
        tags.append("timeout")

    if "incident" in path_lower:
        severity = "sev2"

    return {
        "service": service,
        "severity": severity,
        "tags": sorted(set(tags)),
    }


def build_chunks(docs: list) -> list[dict]:
    chunk_records = []

    for doc in docs:
        inferred = infer_metadata(doc)
        sections = split_markdown_sections(doc.content)

        for section_title, section_text in sections:
            section_chunks = chunk_section(section_title=section_title, text=section_text)

            for chunk in section_chunks:
                chunk_records.append(
                    {
                        "chunk_id": chunk["chunk_id"],
                        "doc_id": doc.doc_id,
                        "parent_id": doc.doc_id,
                        "source": doc.source,
                        "title": doc.title,
                        "text": chunk["text"],
                        "section": chunk["section"],
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"],
                        "path": doc.path,
                        "url": doc.url,
                        "created_at": doc.created_at,
                        "updated_at": doc.updated_at,
                        "service": inferred["service"],
                        "severity": inferred["severity"],
                        "tags": inferred["tags"],
                    }
                )

    return chunk_records


def run_ingestion() -> None:
    docs = load_markdown_files("data/raw")

    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_output_path = processed_dir / "raw_documents.json"
    raw_output_path.write_text(
        json.dumps([doc.model_dump() for doc in docs], indent=2),
        encoding="utf-8",
    )

    chunks = build_chunks(docs)

    chunk_output_path = processed_dir / "chunks.json"
    chunk_output_path.write_text(
        json.dumps(chunks, indent=2),
        encoding="utf-8",
    )

    print(f"Ingested {len(docs)} documents")
    print(f"Built {len(chunks)} chunks")
    print(f"Saved raw docs to {raw_output_path}")
    print(f"Saved chunks to {chunk_output_path}")


