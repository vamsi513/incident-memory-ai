import math


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


def recall_at_k(retrieved_doc_ids: list[str], expected_doc_ids: list[str], k: int) -> float:
    """Fraction of expected documents actually retrieved in the top-k.

    Unlike hit_rate_at_k (which only checks whether *any* expected doc
    appears), this credits partial coverage on multi-answer queries -- a
    query with 3 expected docs that only surfaces 1 of them scores 1/3
    here, not a flat 1.0.
    """
    if not expected_doc_ids:
        return 0.0
    top_k = set(retrieved_doc_ids[:k])
    expected = set(expected_doc_ids)
    return len(expected.intersection(top_k)) / len(expected)


def ndcg_at_k(retrieved_doc_ids: list[str], expected_doc_ids: list[str], k: int) -> float:
    """Binary-relevance NDCG@k: relevance is 1 for an expected doc, 0 otherwise.

    Multiple expected docs are treated as equally relevant (no graded
    relevance in this dataset), so the ideal ranking is simply every
    expected doc packed into the first min(len(expected), k) positions.
    """
    expected = set(expected_doc_ids)
    if not expected:
        return 0.0

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, doc_id in enumerate(retrieved_doc_ids[:k], start=1)
        if doc_id in expected
    )
    ideal_hits = min(len(expected), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0
