import re

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_hybrid_search_service
from core.exceptions import RetrievalError
from core.logging import get_logger
from schemas.search import SearchRequest, SearchResponse
from services.hybrid_search_service import HybridSearchService

router = APIRouter(tags=["search"])
logger = get_logger(__name__)

_PII_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b|\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", re.I)


def _safe_query(query: str) -> str:
    masked = _PII_RE.sub("[redacted]", query)
    return masked[:120] + "…" if len(masked) > 120 else masked


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    payload: SearchRequest,
    search_service: HybridSearchService = Depends(get_hybrid_search_service),
) -> SearchResponse:
    try:
        logger.info("search_request_received", query=_safe_query(payload.query), top_k=payload.top_k)
        result = await search_service.search(payload)
        logger.info(
            "search_request_completed",
            query=payload.query,
            result_count=len(result.results),
        )
        return result
    except RetrievalError as exc:
        logger.error("search_request_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Retrieval pipeline failed",
        ) from exc
