# IncidentMemory AI

[![CI](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A production-style Retrieval-Augmented Generation (RAG) system for engineering incident knowledge. Acts as an operational memory layer for postmortems, runbooks, and architecture documents — letting engineers query prior failure modes, root causes, mitigations, and recovery procedures with grounded citations.

The engineering focus is on retrieval quality over simplicity: hybrid BM25 + FAISS dense search, Reciprocal Rank Fusion, cross-encoder reranking, section-aware scoring, and a query-rewriting layer — all benchmarked with MLflow-tracked evaluation.

---

## Live Demo

API live at **[http://23.21.42.197/incidentmemai-ui/](http://23.21.42.197/incidentmemai-ui/)**

---

## Architecture

```
  User Query
      │
      ▼
  FastAPI App (app/main.py)
  ├── Prompt injection detection
  ├── PII masking
      │
      ▼
  Retrieval Pipeline (retrieval/pipeline.py)
  ┌─────────────────────────────────────────────────────┐
  │  Query Rewriting (query_rewrite.py)                 │
  │  ┌──────────────────┐  ┌────────────────────────┐   │
  │  │ BM25 keyword     │  │ FAISS dense vector     │   │
  │  │ (bm25_store.py)  │  │ (vector_store.py)      │   │
  │  │ rank-bm25/Okapi  │  │ all-MiniLM-L6-v2       │   │
  │  └──────────────────┘  └────────────────────────┘   │
  │            └──────────────────┘                      │
  │         Reciprocal Rank Fusion (hybrid.py)           │
  │                    │                                 │
  │         Section candidate injection                  │
  │                    │                                 │
  │       Cross-Encoder Reranking (cross_encoder.py)     │
  │       ms-marco-MiniLM-L-6-v2                         │
  │                    │                                 │
  │         Section score boosting (postprocess.py)      │
  └─────────────────────────────────────────────────────┘
      │
      ▼
  LLM Generation (app/llm.py)
  OpenAI / Anthropic / Mistral
      │
      ▼
  Grounded Answer + Citations
```

---

## Features

- **Hybrid retrieval** — BM25 keyword search fused with FAISS dense vector search via Reciprocal Rank Fusion (RRF)
- **Cross-encoder reranking** — `ms-marco-MiniLM-L-6-v2` reranks fused candidates before generation
- **Query rewriting** — expands queries with synonym variants to improve BM25 recall on paraphrased inputs
- **Section-aware scoring** — post-rerank score boosts based on document section type matched to query intent
- **FAISS vector store** — `IndexFlatIP` with normalized embeddings (cosine similarity) persisted to disk
- **Parent-document retrieval** — chunk-level retrieval expanded to full parent document context for richer answers
- **Multi-provider LLM** — OpenAI, Anthropic, and Mistral backends, configurable via `LLM_PROVIDER`
- **Prompt injection detection** — query-level injection guards and PII masking on the API layer
- **MLflow evaluation tracking** — `scripts/run_evals.py` logs Recall@K, MRR, per-query latency, and run parameters per evaluation run
- **Retrieval evaluation harness** — 12-query labeled eval dataset across 10 documents covering paraphrased, specific, and cross-document queries
- **Async service layer** — FastAPI with structured logging via structlog and OpenTelemetry tracing stubs
- **Containerised** — Docker Compose stack with Postgres, Redis, and Qdrant for local infrastructure

---

## Evaluation Results

Evaluated on 12 labeled queries against 10 documents (incident reports, runbooks, architecture docs) using the `scripts/run_evals.py` harness.

| Metric | Score |
|---|---|
| Recall@1 | 0.75 |
| Recall@3 | 1.00 |
| Recall@5 | 1.00 |
| MRR | 0.85 |

Queries include paraphrased variants (vocabulary mismatch from document text) and cross-document queries that require retrieving from multiple relevant sources. All metrics computed against ground-truth `expected_doc_ids` using the `evals/metrics.py` implementation. Run tracked and logged to MLflow.

---

## Tech Stack

| Category | Technology |
|---|---|
| Vector Store | FAISS (faiss-cpu, IndexFlatIP) |
| BM25 Search | rank-bm25 (BM25Okapi) |
| Embeddings | sentence-transformers — all-MiniLM-L6-v2 |
| Reranker | sentence-transformers — ms-marco-MiniLM-L-6-v2 |
| LLM Backends | OpenAI, Anthropic, Mistral |
| Backend API | FastAPI 0.115.0 + uvicorn |
| Data Validation | Pydantic v2 |
| Experiment Tracking | MLflow |
| Observability | structlog, OpenTelemetry (wired) |
| Async Queue | Redis + arq |
| Storage | Postgres (asyncpg + SQLAlchemy) |
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

### 2. Start infrastructure (Postgres + Redis + Qdrant)

```bash
docker compose up --build
```

### 3. Ingest documents and build the FAISS index

```bash
python -m scripts.run_ingestion
python -m scripts.build_index
```

### 4. Start the app

```bash
uvicorn app.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

### 5. Run tests

```bash
pytest -q
```

### 6. Run retrieval evaluation with MLflow tracking

```bash
python -m scripts.run_evals
```

Results logged to `./mlruns/`. Open the MLflow UI with:

```bash
mlflow ui
```

---

## Environment Variables

```env
# LLM provider (openai | anthropic | mistral)
LLM_PROVIDER=openai
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
MISTRAL_API_KEY=

# Embeddings and reranking
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Database (used by full async API layer)
POSTGRES_DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/incidentmemory

# Redis (used by background workers)
REDIS_URL=redis://localhost:6379/0

# Qdrant (used by services/qdrant_service.py)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=incident_chunks

# MLflow (optional — defaults to local ./mlruns)
MLFLOW_TRACKING_URI=
MLFLOW_EXPERIMENT=incident-memory-retrieval-eval
```

---

## API Endpoints

The deployed app (`app/main.py`) exposes:

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/query` | Hybrid retrieval + LLM generation with citations |

The full async enterprise API (`api/main.py`) exposes:

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/search` | Hybrid search via service layer (no generation) |

---

## Project Structure

```
incident-memory-ai/
├── app/                            # Deployed FastAPI app (Render)
│   ├── main.py                     # /health and /query endpoints
│   ├── generator.py                # Prompt and citation builder
│   ├── llm.py                      # LLM call wrapper
│   └── prompts.py                  # System prompt
├── api/                            # Enterprise API layer (service-oriented)
│   ├── main.py
│   ├── dependencies.py
│   └── routes/search.py            # POST /v1/search
├── retrieval/                      # Core retrieval pipeline
│   ├── pipeline.py                 # Orchestrates full retrieval (BM25 + FAISS + rerank)
│   ├── bm25_store.py               # BM25Okapi keyword search
│   ├── vector_store.py             # FAISS IndexFlatIP dense search
│   ├── embedder.py                 # sentence-transformers encoder
│   ├── hybrid.py                   # Reciprocal Rank Fusion
│   ├── query_rewrite.py            # Query expansion with synonym variants
│   └── postprocess.py              # Section-aware score boosting
├── rerank/
│   └── cross_encoder.py            # ms-marco-MiniLM-L-6-v2 reranker
├── services/                       # Async service layer (used by api/)
│   ├── hybrid_search_service.py
│   ├── bm25_service.py
│   ├── vector_service.py           # FAISS-backed vector search service
│   ├── qdrant_service.py           # Qdrant-backed vector search (production option)
│   ├── rerank_service.py
│   └── parent_retrieval_service.py
├── core/                           # Config, logging, security, tracing
│   ├── config.py
│   ├── llm_factory.py
│   ├── security.py                 # Injection detection, PII masking
│   └── tracing.py
├── ingestion/                      # Document loading and chunking pipeline
│   ├── pipeline.py
│   ├── chunker.py
│   └── connectors/local_files.py
├── schemas/                        # Pydantic contracts
├── eval/
│   ├── ragas_runner.py             # Service-layer retrieval benchmark (hit-rate)
│   └── mlflow_tracker.py          # MLflow wrapper for ragas_runner
├── evals/
│   ├── dataset.json                # 12-query labeled eval dataset
│   └── metrics.py                  # recall_at_k, reciprocal_rank
├── scripts/
│   ├── run_ingestion.py            # Ingest raw docs → chunks.json
│   ├── build_index.py              # chunks.json → FAISS index
│   └── run_evals.py                # Full eval with MLflow tracking
├── data/
│   ├── raw/                        # Source documents (incidents, runbooks, docs)
│   └── processed/                  # FAISS index, chunks, index_records
├── tests/
├── workers/                        # Background task workers (arq + Redis)
├── docker/
├── docker-compose.yml
├── render.yaml
├── Makefile
└── README.md
```

---

## Why This Project

This demonstrates the parts of RAG engineering that matter in production systems:

- **Retrieval architecture** beyond simple vector search — BM25 fusion, cross-encoder reranking, query rewriting, section-aware post-processing
- **Evaluation as a first-class concern** — labeled ground-truth dataset, Recall@K and MRR computed against real retrieval, experiment tracking with MLflow
- **Multiple LLM providers** with a factory pattern — swappable without code changes
- **Typed contracts** and clear service boundaries throughout
- **Production infrastructure** — async workers, Redis queues, Postgres persistence, Docker Compose

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built by [Vamsi Krishna Sadu](https://github.com/vamsi513)
