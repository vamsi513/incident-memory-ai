_SERVICE_TERMS = {"checkout", "search", "database", "latency", "timeout"}


def apply_section_boosts(records: list[dict], query: str) -> list[dict]:
    boosted = []
    query_lower = query.lower()
    asks_for_resolution = any(
        term in query_lower for term in ["fixed", "resolve", "resolved", "mitigation"]
    )
    # Which recognized service terms this query actually names (e.g. both
    # "checkout" and "timeout" for "the checkout timeout incident").
    query_terms = {term for term in _SERVICE_TERMS if term in query_lower}

    for record in records:
        row = dict(record)
        section = (row.get("section") or "").strip().lower()
        base_score = row.get("rerank_score", 0.0)
        boost = 0.0

        # A chunk only earns the resolution/root-cause boost below if it
        # matches every service term the query names, not just any one --
        # otherwise a Mitigation chunk from an unrelated incident that
        # happens to mention "checkout" in passing gets the same flat
        # boost as the chunk that's actually about the queried incident,
        # and the two then compete on nothing but base rerank score, which
        # can flip on tiny floating-point differences between machines.
        # (Same specificity fix as _inject_section_candidates, applied here
        # too since this is a separate boost path with its own blanket
        # section match.)
        if query_terms:
            haystack = " ".join(
                [row.get("doc_id", ""), row.get("title", ""), row.get("text", ""),
                 " ".join(row.get("tags", [])), row.get("service") or ""]
            ).lower()
            specific_enough = all(term in haystack for term in query_terms)
        else:
            specific_enough = True

        # Naming two or more specific service terms together ("checkout
        # timeout", "search latency") is a strong, deterministic signal of
        # which document is actually meant -- more reliable than the cross-
        # encoder's semantic score, which can rate a generically similar
        # chunk from the wrong document just as high or higher. This applies
        # regardless of section, unlike the boosts below, and exists so the
        # right document doesn't have to win purely on a narrow semantic-
        # score margin that can flip between machines.
        if len(query_terms) >= 2 and specific_enough:
            boost += 8.0

        if "root cause" in query_lower and section == "root cause" and specific_enough:
            boost += 3.0
        elif "root cause" in query_lower and section in {"summary", "impact"}:
            boost -= 1.0

        if asks_for_resolution and section in {"mitigation", "mitigation steps"} and specific_enough:
            boost += 6.0
        elif asks_for_resolution and section in {"summary", "impact"}:
            boost -= 2.0
        elif asks_for_resolution and section == "root cause" and specific_enough:
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
