from eval.ragas_runner import run_retrieval_eval
from services.ingestion_service import IngestionService


async def run_ingestion_job(_: dict, base_path: str) -> dict:
    service = IngestionService()
    docs = await service.ingest_directory(base_path)
    return {"ingested_documents": len(docs)}


async def run_eval_job(_: dict) -> dict:
    report = await run_retrieval_eval()
    return report.model_dump()
