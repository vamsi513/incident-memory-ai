def apply_section_boosts(records: list[dict], query: str) -> list[dict]:
    boosted = []
    query_lower = query.lower()
    asks_for_resolution = any(
        term in query_lower for term in ["fixed", "resolve", "resolved", "mitigation"]
    )

    for record in records:
        row = dict(record)
        section = (row.get("section") or "").strip().lower()
        base_score = row.get("rerank_score", 0.0)
        boost = 0.0

        if "root cause" in query_lower and section == "root cause":
            boost += 3.0
        elif "root cause" in query_lower and section in {"summary", "impact"}:
            boost -= 1.0

        if asks_for_resolution and section in {"mitigation", "mitigation steps"}:
            boost += 6.0
        elif asks_for_resolution and section in {"summary", "impact"}:
            boost -= 2.0
        elif asks_for_resolution and section == "root cause":
            boost += 0.5

        if (
            "runbook" in query_lower
            or "steps" in query_lower
            or "checks" in query_lower
        ) and (
            section == "immediate checks"
            or section == "mitigation steps"
            or section == "escalation"
        ):
            boost += 2.0
        elif any(term in query_lower for term in ["runbook", "steps", "checks"]) and section == "symptoms":
            boost -= 0.5

        row["final_score"] = base_score + boost
        boosted.append(row)

    boosted.sort(key=lambda x: x["final_score"], reverse=True)
    return boosted
