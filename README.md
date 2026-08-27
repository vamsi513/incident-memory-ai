# IncidentMemory AI

[![CI](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A production-style Retrieval-Augmented Generation (RAG) system for engineering incident knowledge. Acts as an operational memory layer for postmortems, runbooks, and architecture documents — letting engineers query prior failure modes, root causes, mitigations, and recovery procedures with grounded citations.

The engineering focus is on retrieval quality: hybrid BM25 + FAISS dense search, Reciprocal Rank Fusion, cross-encoder reranking, section-aware post-processing, and query rewriting — all benchmarked with an MLflow-tracked evaluation harness.

---

## Live Demo

API live at **[http://23.21.42.197/incidentmemai-ui/](http://23.21.42.197/incidentmemai-ui/)**

---

## Architecture

The canonical entry point is `api/main.py`, which wires the full retrieval stack:

```
  User Query  →  POST /v1/search  (api/main.py)
                       │
                       ▼
  HybridSearchService  (services/hybrid_search_service.py)
  ┌─────────────────────────────────────────────────────┐
  │  ┌─────────────────┐   ┌──────────────────────────┐ │
  │  │ BM25 keyword    │   │ FAISS dense vector       │ │
  │  │ rank-bm25/Okapi │   │ all-MiniLM-L6-v2 (384d) │ │
  │  │ bm25_service.py │   │ vector_service.py        │ │
  │  └────────┬────────┘   └────────────┬─────────────┘ │
  │           └───────────┬─────────────┘               │
  │              Reciprocal Rank Fusion (k=60)          │
  │                       │                             │
  │           Cross-Encoder Reranking                   │
  │           ms-marco-MiniLM-L-6-v2                    │
  │           (rerank_service.py)                       │
  │                       │                             │
  │           Parent-document grouping                  │
  │           (parent_retrieval_service.py)             │
  └───────────────────────┼─────────────────────────────┘
                          │
                          ▼
  Ranked results with supporting chunks + section summaries
```

The `app/` directory contains a standalone RAG app (`app/main.py`) with LLM generation (`/query` endpoint) that uses the `retrieval/` pipeline directly — useful for quick local testing with `POST /query`.

---

## Features

- **Hybrid retrieval** — BM25 keyword search (rank-bm25/Okapi) fused with FAISS dense vector search (all-MiniLM-L6-v2) via Reciprocal Rank Fusion
- **Cross-encoder reranking** — `ms-marco-MiniLM-L-6-v2` rescores fused candidates before generation
- **Query rewriting** — expands queries with synonym variants to improve BM25 recall on paraphrased inputs
- **Section-aware scoring** — post-rerank boosts tied to section type (root cause, mitigation, immediate checks) matched to query intent
- **FAISS vector store** — `IndexFlatIP` with normalized embeddings (inner product = cosine similarity on unit vectors), persisted to disk
- **Multi-provider LLM generation** — OpenAI, Anthropic, and Mistral backends in `app/llm.py`, switched via `LLM_PROVIDER` env var
- **Injection detection** — rejects queries matching 8 known injection patterns before retrieval
- **MLflow evaluation tracking** — `scripts/run_evals.py` logs Recall@K, MRR, per-query latency, and run parameters per evaluation run
- **Labeled retrieval eval harness** — 12-query ground-truth dataset across 10 documents covering specific, paraphrased, and cross-document queries
- **Async service layer** — full async FastAPI + service layer for microservice deployment, with structlog structured logging throughout
- **arq background workers** — wired in `workers/` for async ingestion and eval jobs (requires Redis; runs alongside Docker Compose stack)

---

## Evaluation Results

Evaluated on 12 labeled queries against 10 documents (6 incident reports, 2 runbooks, 2 architecture docs).

| Metric | Score |
|---|---|
| Recall@1 | 0.75 |
| Recall@3 | 1.00 |
| Recall@5 | 1.00 |
| MRR | 0.85 |

Queries include paraphrased variants (vocabulary mismatch from document text) and cross-document queries requiring retrieval across multiple relevant sources. All metrics computed against ground-truth `expected_doc_ids` using `evals/metrics.py`. Results logged to MLflow.

Run script: `python -m scripts.run_evals`

---

## Tech Stack

| Category | Technology |
|---|---|
| Vector Store | FAISS (faiss-cpu==1.12.0, IndexFlatIP) |
| BM25 Search | rank-bm25==0.2.2 (BM25Okapi) |
| Embeddings | sentence-transformers==3.2.1 — all-MiniLM-L6-v2 |
| Reranker | sentence-transformers==3.2.1 — ms-marco-MiniLM-L-6-v2 |
| LLM Backends | OpenAI, Anthropic, Mistral (app/llm.py) |
| Backend API | FastAPI==0.115.0 + uvicorn |
| Data Validation | Pydantic v2 (==2.12.0) |
| Experiment Tracking | MLflow (>=2.15.0) |
| Structured Logging | structlog==24.4.0 |
| Async Queue | arq==0.26.3 + Redis (local dev / Docker Compose) |
| Storage | Postgres + SQLAlchemy async (local dev / Docker Compose) |
| Containerisation | Docker Compose |
| Language | Python 3.11 |

---

## Screenshots

### Root Cause Lookup
![Root Cause Lookup](docs/screenshots/root-cause-search.png)

### Mitigation Lookup
![Mitigation Lookup](docs/screenshots/checkout-fix.png)

### Retrieved Evidence Panel
![Retrieved Chunks](docs/screenshots/retrieved-chunks.png)

### Evaluation Output
![Evaluation Metrics](docs/screenshots/eval-metrics.png)

---

## Local Development

### 1. Install dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Ingest documents and build the FAISS index

```bash
python -m scripts.run_ingestion
python -m scripts.build_index
```

### 3. Start the app

```bash
uvicorn api.main:app --reload --port 8000
```

Endpoints: `GET /health`, `POST /v1/search`. Docs at `http://localhost:8000/docs`.

To also run the standalone RAG app with LLM generation:

```bash
uvicorn app.main:app --reload --port 8001
```

Endpoints: `GET /health`, `POST /query`.

### 4. Run tests

```bash
pytest tests/ -q
```

### 5. Run retrieval evaluation with MLflow tracking

```bash
python -m scripts.run_evals
mlflow ui
```

### 6. (Optional) Start full infrastructure stack

Postgres + Redis + Qdrant for the async service layer (`api/main.py`):

```bash
docker compose up --build
uvicorn api.main:app --reload --port 8000
```

---

## Environment Variables

```env
# LLM provider — which backend generates answers (openai | anthropic | mistral)
LLM_PROVIDER=openai
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
MISTRAL_API_KEY=

# Retrieval models
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
TOP_K=10
RERANK_TOP_N=5

# Postgres (used by async service layer and Docker Compose stack)
POSTGRES_DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/incidentmemory

# Redis (used by arq workers and Docker Compose stack)
REDIS_URL=redis://localhost:6379/0

# Qdrant (used by services/qdrant_service.py in async service layer)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=incident_chunks

# MLflow (defaults to local ./mlruns if not set)
MLFLOW_TRACKING_URI=
MLFLOW_EXPERIMENT=incident-memory-retrieval-eval
```

---

## API Endpoints

**Enterprise search API** (`api/main.py` — Dockerfile / Docker Compose / EC2):

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/v1/search` | BM25 + FAISS + CrossEncoder hybrid search, ranked parent-doc results |

**Standalone RAG app** (`app/main.py` — local dev):

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/query` | Retrieval + LLM generation with numbered citations |

---

## Project Structure

```
incident-memory-ai/
├── app/                            # Deployed FastAPI app (Render)
│   ├── main.py                     # /health + /query, injection check, PII redaction
│   ├── llm.py                      # Multi-provider generation (OpenAI / Anthropic / Mistral)
│   ├── generator.py                # Context builder and citation formatter
│   └── prompts.py                  # System prompt
├── api/                            # Async service layer (Docker Compose deployment)
│   ├── main.py                     # FastAPI app with structured logging
│   ├── dependencies.py             # DI wiring for HybridSearchService
│   └── routes/search.py            # POST /v1/search
├── retrieval/                      # Core retrieval pipeline (used by app/)
│   ├── pipeline.py                 # Orchestrates full retrieval
│   ├── bm25_store.py               # BM25Okapi keyword search
│   ├── vector_store.py             # FAISS IndexFlatIP dense search
│   ├── embedder.py                 # sentence-transformers encoder
│   ├── hybrid.py                   # Reciprocal Rank Fusion
│   ├── query_rewrite.py            # Synonym-based query expansion
│   └── postprocess.py              # Section-aware score boosts
├── rerank/
│   └── cross_encoder.py            # CrossEncoder reranker
├── services/                       # Async service layer (used by api/)
│   ├── hybrid_search_service.py    # Orchestrates BM25 + FAISS + RRF + rerank
│   ├── bm25_service.py
│   ├── vector_service.py           # FAISS-backed async vector search
│   ├── qdrant_service.py           # Qdrant-backed async vector search (alternative)
│   ├── rerank_service.py
│   └── parent_retrieval_service.py # Builds parent summaries dynamically from index_records.json
├── core/
│   ├── config.py                   # Pydantic settings from env
│   ├── security.py                 # Injection detection (8 patterns), PII redaction (email/phone/SSN/card)
│   ├── logging.py                  # structlog configuration
│   ├── tracing.py                  # traced_span stub (OpenTelemetry placeholder)
│   └── llm_factory.py              # LLM-as-judge: scores answer grounding via OpenAI or Anthropic
├── ingestion/                      # Document loading and chunking
│   ├── pipeline.py                 # Ingest raw docs → chunks with metadata inference
│   ├── chunker.py
│   └── connectors/local_files.py   # Loads .md files, doc_id = filename stem
├── schemas/                        # Pydantic request/response models
├── evals/
│   ├── dataset.json                # 12 labeled queries with expected_doc_ids
│   └── metrics.py                  # recall_at_k, reciprocal_rank implementations
├── eval/
│   ├── ragas_runner.py             # 3-sample hit-rate benchmark (service layer)
│   └── mlflow_tracker.py           # MLflow wrapper for ragas_runner
├── scripts/
│   ├── run_ingestion.py            # Loads data/raw/ → data/processed/chunks.json
│   ├── build_index.py              # chunks.json → FAISS index + index_records.json
│   └── run_evals.py                # Full eval: Recall@K, MRR, latency → MLflow
├── workers/
│   ├── tasks.py                    # arq task definitions (ingestion, eval)
│   └── settings.py                 # arq WorkerSettings with Redis connection
├── data/
│   ├── raw/                        # 10 source documents (incidents, runbooks, docs)
│   └── processed/                  # FAISS index, chunks.json, index_records.json
├── tests/
├── docker/
├── docker-compose.yml              # Postgres + Redis + Qdrant for local dev
├── render.yaml                     # Render deployment config
├── Makefile
└── README.md
```

---

## CI/CD — GitHub Actions auto-deploy

Every push to `main` triggers a GitHub Actions pipeline:

1. Installs dependencies, runs ruff lint and security scan
2. Builds the Docker image
3. Runs the test suite (unit and security tests; integration tests require live services)
4. Deploys to AWS EC2 via SSH — checks out the exact tested commit, rebuilds, and restarts the container
5. Runs a health check loop (`GET /health`) — if the new container fails to start, the previous image is automatically restored

Required GitHub Secrets: `EC2_HOST`, `EC2_SSH_KEY`

## Why This Project

- **Retrieval architecture** beyond simple vector search — BM25 fusion, cross-encoder reranking, query rewriting, section-aware post-processing, all in a single coherent pipeline
- **Evaluation as a first-class concern** — labeled ground-truth dataset, Recall@K and MRR computed against real retrieval, every run tracked with MLflow
- **Typed contracts and clear boundaries** — Pydantic schemas at every layer, clean service boundaries between retrieval, reranking, and generation
- **Two deployment patterns** — a lightweight single-process app (Render) and a full async microservice stack (Docker Compose)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built by [Vamsi Krishna Sadu](https://github.com/vamsi513)
