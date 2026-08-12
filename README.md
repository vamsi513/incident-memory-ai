# IncidentMemory AI

[![CI](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A production-style Retrieval-Augmented Generation (RAG) system for engineering incident knowledge. Acts as an operational memory layer for postmortems, runbooks, and architecture documents — allowing engineers to query prior failure modes, root causes, mitigations, and recovery procedures with grounded citations.

This project is intentionally positioned beyond a generic PDF chatbot. The engineering focus is on retrieval quality, hybrid search, reranking, evaluation, observability, and system design decisions relevant to AI/ML systems roles.

---

## Live Demo

API live at **[http://23.21.42.197/incidentmemai-ui/](http://23.21.42.197/incidentmemai-ui/)**

---

## Architecture

```
  User Query
      │
      ▼
  FastAPI Layer (api/)
      │
      ▼
  Hybrid Search (services/hybrid_search_service.py)
  ┌───────────────────────────────────────────┐
  │  BM25 keyword search (bm25_service.py)    │
  │  + Dense vector search (qdrant_service.py)│
  │  → RRF fusion                             │
  └───────────────────────────────────────────┘
      │
      ▼
  Cross-Encoder Reranking (rerank_service.py)
  ms-marco-MiniLM-L-6-v2
      │
      ▼
  Parent Document Retrieval (parent_retrieval_service.py)
      │
      ▼
  LLM Generation (core/llm_factory.py)
  OpenAI / Anthropic / Mistral
      │
      ▼
  Grounded Answer + Citations
```

---

## Features

- **Hybrid retrieval** — BM25 keyword search fused with Qdrant dense vector search via Reciprocal Rank Fusion (RRF)
- **Cross-encoder reranking** — `ms-marco-MiniLM-L-6-v2` reranks candidate chunks before generation
- **Qdrant vector store** — persistent cloud-scale vector index with cosine similarity search, auto-collection creation
- **Parent-document retrieval** — returns full parent context after chunk-level retrieval for richer answers
- **Multi-provider LLM** — OpenAI, Anthropic (Claude), and Mistral backends configurable via `LLM_PROVIDER`
- **Prompt injection detection** — query-level PII masking and injection guards on the API layer
- **MLflow evaluation tracking** — `eval/mlflow_tracker.py` logs hit-rate metrics, run parameters, and result artifacts per evaluation run
- **Retrieval evaluation harness** — `eval/ragas_runner.py` benchmarks retrieval quality with configurable sample sets
- **Async FastAPI** — full async service layer with structured logging and OpenTelemetry tracing placeholders
- **Containerised** — Docker Compose stack with Postgres, Redis, and Qdrant for local development

---

## Tech Stack

| Category | Technology |
|---|---|
| Vector Store | Qdrant 1.12.1 |
| BM25 Search | rank-bm25 |
| Reranker | sentence-transformers (ms-marco-MiniLM-L-6-v2) |
| Embeddings | sentence-transformers 3.2.1 |
| LLM Backends | OpenAI, Anthropic, Mistral |
| Backend API | FastAPI 0.115.0 + uvicorn |
| Data Validation | Pydantic v2 |
| Async Queue | Redis + arq |
| Storage | Postgres (asyncpg + SQLAlchemy) |
| Experiment Tracking | MLflow |
| Evaluation | Custom retrieval hit-rate harness |
| Observability | OpenTelemetry (wired), structlog |
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

### 3. Start the API

```bash
uvicorn api.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

### 4. Run tests

```bash
pytest -q
```

### 5. Run retrieval evaluation

```bash
python -m eval.ragas_runner
```

### 6. Run evaluation with MLflow tracking

```bash
python -m eval.mlflow_tracker
```

Results logged to `./mlruns/` (or `MLFLOW_TRACKING_URI` if set). Open the MLflow UI with:

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

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=incident_memory

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/incidentmemory

# Redis
REDIS_URL=redis://localhost:6379/0

# MLflow (optional)
MLFLOW_TRACKING_URI=
MLFLOW_EXPERIMENT=incident-memory-eval
```

---

## Project Structure

```
incident-memory-ai/
├── api/                            # FastAPI routes and dependency wiring
│   ├── main.py
│   ├── dependencies.py
│   └── routes/
├── app/                            # Streamlit UI
├── core/                           # Config, Qdrant client, LLM factory, logging
│   ├── config.py
│   ├── qdrant.py
│   ├── llm_factory.py
│   ├── security.py
│   └── tracing.py
├── services/                       # Retrieval pipeline
│   ├── bm25_service.py             # BM25 keyword search
│   ├── vector_service.py           # In-memory vector search (dev/test)
│   ├── qdrant_service.py           # Qdrant-backed vector search (production)
│   ├── hybrid_search_service.py    # BM25 + dense fusion with RRF
│   ├── rerank_service.py           # Cross-encoder reranking
│   ├── parent_retrieval_service.py # Parent-document context expansion
│   └── ingestion_service.py        # Document ingestion pipeline
├── schemas/                        # Pydantic request/response contracts
├── eval/
│   ├── ragas_runner.py             # Retrieval benchmark (hit-rate)
│   └── mlflow_tracker.py           # MLflow-wrapped eval runner
├── workers/                        # Background task workers
├── ingestion/                      # Document loading and chunking
├── retrieval/                      # Retrieval utilities
├── rerank/                         # Reranker utilities
├── data/                           # Sample documents
├── docs/
│   └── screenshots/                # UI screenshots
├── tests/
├── docker/
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── README.md
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/query` | Hybrid search + generation |
| `POST` | `/ingest` | Ingest documents |

---

## Why This Project

This demonstrates the parts of RAG engineering that matter in production systems:

- **Retrieval architecture** beyond simple vector search — BM25 fusion, reranking, parent-document expansion
- **Qdrant** for persistent, scalable vector storage replacing in-memory stores
- **Multiple LLM providers** with a factory pattern — swappable without code changes
- **Evaluation as a first-class concern** with MLflow tracking for regression detection
- **Typed contracts** and clear service boundaries throughout
- **Production infrastructure** — async workers, Redis queues, Postgres persistence, Docker Compose

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built by [Vamsi Krishna Sadu](https://github.com/vamsi513)
