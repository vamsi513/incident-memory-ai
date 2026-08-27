FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface

RUN addgroup --system appgroup && adduser --system --ingroup appgroup --uid 1000 appuser

COPY requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt

RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY api ./api
COPY app ./app
COPY core ./core
COPY retrieval ./retrieval
COPY rerank ./rerank
COPY ingestion ./ingestion
COPY services ./services
COPY schemas ./schemas
COPY workers ./workers
COPY data ./data

RUN chown -R appuser:appgroup /app
USER appuser

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"]
