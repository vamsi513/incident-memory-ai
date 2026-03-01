from app.prompts import SYSTEM_PROMPT


def build_context(records: list[dict]) -> str:
    rows = []
    for i, record in enumerate(records, start=1):
        rows.append(
            f"[{i}] "
            f"title={record.get('title')} | "
            f"section={record.get('section')} | "
            f"source={record.get('source')} | "
            f"path={record.get('path')} | "
            f"url={record.get('url')}\n"
            f"{record.get('text')}"
        )
    return "\n\n".join(rows)


def build_user_prompt(query: str, records: list[dict]) -> str:
    context = build_context(records)

    return f"""
Question:
{query}

Retrieved Evidence:
{context}

Answer only from the evidence above.
If the evidence is insufficient, say: "I don't know based on the retrieved incident memory."
Cite claims using [1], [2], etc.
"""


def build_citations(records: list[dict]) -> list[str]:
    citations = []
    for i, record in enumerate(records, start=1):
        citations.append(
            f"[{i}] {record.get('title')} - section: {record.get('section')} - path: {record.get('path')}"
        )
    return citations

