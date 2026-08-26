import json
from pathlib import Path

from rerank.cross_encoder import Reranker
from retrieval.bm25_store import BM25Store
from retrieval.embedder import Embedder
from retrieval.hybrid import reciprocal_rank_fusion
from retrieval.postprocess import apply_section_boosts
from retrieval.query_rewrite import rewrite_query
from retrieval.vector_store import FaissStore

# ── Module-level singletons (loaded once, reused across all requests) ─────────
_embedder: Embedder | None = None
_vector_store: FaissStore | None = None
_bm25_store: BM25Store | None = None
_reranker: Reranker | None = None
_records: list[dict] | None = None


def _get_pipeline() -> tuple[Embedder, FaissStore, BM25Store, Reranker, list[dict]]:
    global _embedder, _vector_store, _bm25_store, _reranker, _records
    if _records is None:
        records_path = Path("data/processed/index_records.json")
        _records = json.loads(records_path.read_text(encoding="utf-8"))
    if _embedder is None:
        _embedder = Embedder()
    if _vector_store is None:
        _vector_store = FaissStore.load("data/processed")
    if _bm25_store is None:
        _bm25_store = BM25Store(
            texts=[r["text"] for r in _records],
            records=_records,
        )
    if _reranker is None:
        _reranker = Reranker()
    return _embedder, _vector_store, _bm25_store, _reranker, _records


def _dedupe_records(records: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()

    for record in records:
        key = record["chunk_id"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)

    return deduped


def _inject_section_candidates(records: list[dict], query: str) -> list[dict]:
    query_lower = query.lower()
    sections_to_prioritize: set[str] = set()

    if "root cause" in query_lower:
        sections_to_prioritize.add("root cause")

    if any(term in query_lower for term in ["fixed", "resolve", "resolved", "mitigation"]):
        sections_to_prioritize.update({"mitigation", "mitigation steps"})

    if any(term in query_lower for term in ["runbook", "steps", "checks"]):
        sections_to_prioritize.update({"immediate checks", "mitigation steps", "escalation"})

    if not sections_to_prioritize:
        return []

    service_terms = {"checkout", "search", "database", "latency", "timeout"}
    query_terms = {term for term in service_terms if term in query_lower}

    injected = []
    for record in records:
        section = (record.get("section") or "").strip().lower()
        if section not in sections_to_prioritize:
            continue

        haystacks = " ".join(
            [
                record.get("doc_id", ""),
                record.get("title", ""),
                record.get("text", ""),
                " ".join(record.get("tags", [])),
                record.get("service") or "",
            ]
        ).lower()

        if query_terms and not any(term in haystacks for term in query_terms):
            continue

        injected.append(record)

    return injected


def run_retrieval(query: str, top_k: int = 5) -> list[dict]:
    embedder, vector_store, bm25_store, reranker, records = _get_pipeline()

    all_result_sets = []
    rewritten_queries = rewrite_query(query)

    for rewritten_query in rewritten_queries:
        query_embedding = embedder.encode([rewritten_query])[0]
        vector_results = vector_store.search(query_embedding=query_embedding, top_k=12)
        bm25_results = bm25_store.search(query=rewritten_query, top_k=12)
        all_result_sets.append(vector_results)
        all_result_sets.append(bm25_results)

    hybrid_results = reciprocal_rank_fusion(all_result_sets)[:12]
    hybrid_results.extend(_inject_section_candidates(records, query))
    hybrid_results = _dedupe_records(hybrid_results)

    reranked_results = reranker.rerank(
        query=query,
        records=hybrid_results,
        top_n=min(len(hybrid_results), 12),
    )
    final_results = apply_section_boosts(reranked_results, query=query)[:top_k]

    return final_results

