import time
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.generator import build_citations, build_user_prompt
from app.llm import generate_answer
from app.prompts import SYSTEM_PROMPT
from app.schemas import QueryRequest, QueryResponse
from core.config import settings
from core.logging import configure_logging, get_logger
from core.security import detect_prompt_injection, mask_pii
from retrieval.pipeline import run_retrieval

configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(title="IncidentMemory AI")

_INDEX_FILES = [
    Path("data/processed/index.faiss"),
    Path("data/processed/index_records.json"),
    Path("data/processed/chunks.json"),
]


def _provider_key_present() -> bool:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "anthropic":
        return bool(settings.anthropic_api_key)
    if provider == "mistral":
        return bool(settings.mistral_api_key)
    return False


@app.get("/health")
def health() -> dict:
    missing_files = [str(p) for p in _INDEX_FILES if not p.exists()]
    index_ok = len(missing_files) == 0
    llm_key_ok = _provider_key_present()

    status = "ok" if (index_ok and llm_key_ok) else "degraded"

    return {
        "status": status,
        "index_loaded": index_ok,
        "missing_index_files": missing_files,
        "llm_provider": settings.llm_provider,
        "llm_key_configured": llm_key_ok,
    }


@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest) -> QueryResponse:
    if detect_prompt_injection(request.query):
        logger.warning("query_rejected_prompt_injection", query=mask_pii(request.query))
        raise HTTPException(
            status_code=400,
            detail="Query rejected: contains a disallowed instruction pattern.",
        )

    masked_query = mask_pii(request.query)
    logger.info("query_received", query=masked_query)

    t_start = time.perf_counter()

    try:
        t_retrieval_start = time.perf_counter()
        retrieved_chunks = run_retrieval(request.query, top_k=5)
        retrieval_ms = round((time.perf_counter() - t_retrieval_start) * 1000, 1)
    except Exception as exc:
        total_ms = round((time.perf_counter() - t_start) * 1000, 1)
        logger.error(
            "retrieval_failed",
            query=masked_query,
            error=str(exc),
            error_type=type(exc).__name__,
            elapsed_ms=total_ms,
        )
        raise HTTPException(status_code=500, detail="Retrieval pipeline error.")

    user_prompt = build_user_prompt(request.query, retrieved_chunks)
    answer = generate_answer(SYSTEM_PROMPT, user_prompt)
    citations = build_citations(retrieved_chunks)

    total_ms = round((time.perf_counter() - t_start) * 1000, 1)
    logger.info(
        "query_completed",
        query=masked_query,
        retrieved_count=len(retrieved_chunks),
        retrieval_ms=retrieval_ms,
        total_ms=total_ms,
    )

    return QueryResponse(
        answer=answer,
        citations=citations,
        retrieved_chunks=retrieved_chunks,
    )
