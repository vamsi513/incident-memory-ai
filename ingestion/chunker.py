import re
import uuid
from typing import Any

HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    matches = list(HEADER_PATTERN.finditer(text))

    if not matches:
        return [("untitled", text.strip())]

    sections = []
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        if body:
            sections.append((title, body))

    return sections


def chunk_section(
    section_title: str,
    text: str,
    max_chars: int = 1200,
    overlap: int = 200,
) -> list[dict[str, Any]]:
    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "section": section_title,
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                }
            )

        if end == len(text):
            break

        start = end - overlap

    return chunks

