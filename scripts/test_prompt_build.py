import json
from pathlib import Path

from app.generator import build_citations, build_user_prompt


def main() -> None:
    query = "What fixed the checkout timeout incident?"
    records = json.loads(Path("data/processed/index_records.json").read_text(encoding="utf-8"))

    selected = [r for r in records if r["doc_id"] == "incident_2025_01_checkout_timeout"][:3]

    prompt = build_user_prompt(query, selected)
    citations = build_citations(selected)

    print("=== Prompt ===")
    print(prompt)
    print("\n=== Citations ===")
    for citation in citations:
        print(citation)


if __name__ == "__main__":
    main()

