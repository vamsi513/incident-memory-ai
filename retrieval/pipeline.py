import json
from pathlib import Path

from rerank.cross_encoder import Reranker
from retrieval.bm25_store import BM25Store
from retrieval.embedder import Embedder
from retrieval.hybrid import reciprocal_rank_fusion
from retrieval.postprocess import apply_section_boosts
from retrieval.query_rewrite import rewrite_query
from retrieval.vector_store import FaissStore


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
    records_path = Path("data/processed/index_records.json")
    records = json.loads(records_path.read_text(encoding="utf-8"))

    embedder = Embedder()
    vector_store = FaissStore.load("data/processed")
    bm25_store = BM25Store(
        texts=[record["text"] for record in records],
        records=records,
    )

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

    reranker = Reranker()
    reranked_results = reranker.rerank(
        query=query,
        records=hybrid_results,
        top_n=min(len(hybrid_results), 12),
    )
    final_results = apply_section_boosts(reranked_results, query=query)[:top_k]

    return final_results

