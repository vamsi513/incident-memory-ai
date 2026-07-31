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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest) -> QueryResponse:
    if detect_prompt_injection(request.query):
        logger.warning("query_rejected_prompt_injection", query=mask_pii(request.query))
        raise HTTPException(
            status_code=400,
            detail="Query rejected: contains a disallowed instruction pattern.",
        )

    logger.info("query_received", query=mask_pii(request.query))

    retrieved_chunks = run_retrieval(request.query, top_k=5)
    user_prompt = build_user_prompt(request.query, retrieved_chunks)
    answer = generate_answer(SYSTEM_PROMPT, user_prompt)
    citations = build_citations(retrieved_chunks)

    logger.info(
        "query_completed",
        query=mask_pii(request.query),
        retrieved_count=len(retrieved_chunks),
    )

    return QueryResponse(
        answer=answer,
        citations=citations,
        retrieved_chunks=retrieved_chunks,
    )
