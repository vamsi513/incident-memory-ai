from fastapi import FastAPI

from app.generator import build_citations, build_user_prompt
from app.llm import generate_answer
from app.prompts import SYSTEM_PROMPT
from app.schemas import QueryRequest, QueryResponse
from core.logging import setup_logging
from retrieval.pipeline import run_retrieval

logger = setup_logging()

app = FastAPI(title="IncidentMemory AI")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest) -> QueryResponse:
    logger.info("query_received", query=request.query)

    retrieved_chunks = run_retrieval(request.query, top_k=5)
    user_prompt = build_user_prompt(request.query, retrieved_chunks)
    answer = generate_answer(SYSTEM_PROMPT, user_prompt)
    citations = build_citations(retrieved_chunks)

    logger.info(
        "query_completed",
        query=request.query,
        retrieved_count=len(retrieved_chunks),
    )

    return QueryResponse(
        answer=answer,
        citations=citations,
        retrieved_chunks=retrieved_chunks,
    )
