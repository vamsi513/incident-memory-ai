def hit_rate_at_k(retrieved_doc_ids: list[str], expected_doc_ids: list[str], k: int) -> float:
    """Returns 1.0 if any expected document appears in the top-k results, else 0.0 (hit rate, not recall)."""
    top_k = set(retrieved_doc_ids[:k])
    expected = set(expected_doc_ids)
    return 1.0 if expected.intersection(top_k) else 0.0


def reciprocal_rank(retrieved_doc_ids: list[str], expected_doc_ids: list[str]) -> float:
    expected = set(expected_doc_ids)
    for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
        if doc_id in expected:
            return 1.0 / rank
    return 0.0
