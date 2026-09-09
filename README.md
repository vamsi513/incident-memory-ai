# IncidentMemory AI

[![CI](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/vamsi513/incident-memory-ai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A production-inspired Retrieval-Augmented Generation (RAG) system for engineering incident knowledge. Acts as an operational memory layer for postmortems, runbooks, and architecture documents — letting engineers query prior failure modes, root causes, mitigations, and recovery procedures with grounded citations.

The engineering focus is on retrieval quality: hybrid BM25 + FAISS dense search, Reciprocal Rank Fusion, cross-encoder reranking, section-aware post-processing, and query rewriting — all benchmarked with an MLflow-tracked evaluation harness.

---

## Recent Improvements

The live API previously served BM25 and vector search from 4 hardcoded records instead of the fully ingested corpus, which also hid a Reciprocal Rank Fusion bug (a single-source hit could keep its raw retrieval score instead of a proper RRF score, letting it outrank chunks both retrievers actually agreed on). Both are fixed:

- **Real corpus wired into search** — `services/bm25_service.py` and `services/vector_service.py` now index the full 46-chunk ingested corpus (`data/processed/chunks.json`) instead of a 4-record in-code stub
- **RRF fusion bug fixed** — fusion now accumulates pure rank-based scores; it no longer lets a vector-only hit's raw cosine similarity leak into its fused rank
- **Metadata filters actually apply** — `service` / `severity` / `source` filters were accepted by the API and rendered in the UI but silently ignored; they now filter results, with dropdown options pulled live from `GET /v1/facets`
- **Relevance scores normalized correctly** — parent and per-chunk relevance now run through the same sigmoid, and results below a relevance floor are dropped instead of shown as low-confidence noise
- **Mobile layout fixed**, dead Qdrant scaffolding removed, and the CSP tightened to same-origin only

---

## Live Demo

**Dashboard:** [https://incidentmemory-platformvercelapp.vercel.app](https://incidentmemory-platformvercelapp.vercel.app)

**API:** `http://23.21.42.197:8002` — `GET /health`, `POST /v1/search`

![Hybrid search results with relevance scores and source badges](docs/screenshot.png)

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
- **Multi-provider LLM generation** — OpenAI, Anthropic, and Mistral backends in `app/llm.py`, switched via `LLM_PROVIDER` env var. Lives in the separate `app/main.py` FastAPI app (a `/query` endpoint that retrieves *and* generates a grounded, cited answer), deployed as its own service (`incidentmemai-app`, port 8003) alongside the retrieval-only `api.main:app` (`incidentmemai-api`, port 8002) — the Streamlit UI talks to the former, the `/v1/search` demo hits the latter
- **Injection detection** — rejects queries matching 8 known injection patterns before retrieval
- **API rate limiting** — 20 requests/minute per IP on `/v1/search`, in-process (correct for the current single-instance deployment)
- **MLflow evaluation tracking** — `scripts/run_evals.py` logs Hit Rate@K, MRR, per-query latency, and run parameters per evaluation run
- **Labeled retrieval eval harness** — 60-query ground-truth dataset across 40 documents covering specific, paraphrased, cross-document, and deliberately ambiguous queries
- **pgvector as an alternative dense backend** — `retrieval/pgvector_store.py`, same shape as the FAISS store, backed by a real `document_chunks` table (see Evaluation Results below for how it compares)
- **Citations and a no-answer path** — `app/main.py`'s `/query` endpoint cites sources with `[1]`, `[2]` markers and returns a fixed refusal phrase when retrieved evidence doesn't actually answer the question, verified against real LLM calls in `tests/test_query_citations.py`
- **Async service layer** — full async FastAPI + service layer for microservice deployment, with structlog structured logging throughout
- **arq background workers** — wired in `workers/` for async ingestion and eval jobs (requires Redis; runs alongside the Docker Compose stack). Not part of the public EC2 deployment, which runs the API container alone with no Redis or worker process

---

## Evaluation Results

Evaluated on 60 labeled queries against 40 documents (24 incident reports, 8 runbooks, 8 architecture docs).

| Metric | Score |
|---|---|
| Hit Rate@1 | 0.7833 |
| Hit Rate@3 | 0.9667 |
| Hit Rate@5 | 0.9833 |
| MRR | 0.8681 |

Exact values pulled from MLflow, not rounded console output. Queries include paraphrased variants (vocabulary mismatch from document text), cross-document queries requiring retrieval across multiple relevant sources, and deliberately ambiguous queries with more than one valid answer — the set is built to be genuinely hard to get a perfect score on, not tuned to look good. All metrics computed against ground-truth `expected_doc_ids` using `evals/metrics.py`, run via `python -m scripts.run_evals` against the same `HybridSearchService` that serves the live API. Results logged to MLflow.

Run script: `python -m scripts.run_evals`

### Retrieval ablation: BM25 vs. dense vs. hybrid vs. hybrid+reranking

Same 60 queries, four configurations built from the actual production services (`scripts/run_ablation_eval.py`), each assembled into doc-level results the same way:

| Configuration | Hit Rate@5 | Recall@5 | MRR | NDCG@10 |
|---|---|---|---|---|
| BM25 only | 0.950 | 0.933 | 0.816 | 0.839 |
| Dense only (FAISS) | 0.950 | 0.944 | 0.861 | 0.884 |
| Hybrid (RRF, no rerank) | 0.967 | 0.947 | 0.855 | 0.875 |
| **Hybrid + reranking (production)** | **0.983** | **0.969** | **0.868** | **0.888** |

Every metric improves monotonically as components are added, and the full pipeline wins on all four. Recall@K and NDCG@K (added alongside this ablation — the metrics above only had hit-rate and MRR before, neither of which credits partial coverage on multi-answer queries) live in `evals/metrics.py`. Full raw results: `evals/results/ablation_60query_results.json`.

A pgvector-backed dense store (`retrieval/pgvector_store.py`) exists as a second dense backend alongside FAISS — same 384-dim embeddings, verified against a real query returning correct, score-differentiated results — but the ablation numbers above use FAISS, the store the live API actually runs.

### Retrieval latency

p50 28.67ms, p90 57.89ms, **p95 79.6ms**, p99 114.89ms — 180 real measurements (60 queries × 3 repeats) against the production `HybridSearchService`, via `scripts/measure_latency.py`. Full results: `evals/results/latency_measurement.json`.

### Citations and no-answer behavior

Verified against real LLM calls (`tests/test_query_citations.py`, skipped automatically if no provider key is configured): an answerable query gets a factually correct answer citing real retrieved sources; a genuinely out-of-corpus query (tested with both a GDPR-request and a cafeteria-menu question) gets the exact configured refusal, *"I don't know based on the retrieved incident memory,"* even though the retriever still returns its usual top-5 chunks — the refusal comes from the LLM following the prompt, not a relevance-score cutoff.

---

## Tech Stack

| Category | Technology |
|---|---|
| Vector Store | FAISS (faiss-cpu==1.12.0, IndexFlatIP) |
| BM25 Search | rank-bm25==0.2.2 (BM25Okapi) |
| Embeddings | sentence-transformers==3.2.1 — all-MiniLM-L6-v2 |
| Reranker | sentence-transformers==3.2.1 — ms-marco-MiniLM-L-6-v2 |
| LLM Backends | OpenAI, Anthropic, Mistral (app/llm.py) |
| Backend API | FastAPI==0.141.1 + uvicorn |
| Data Validation | Pydantic v2 (==2.12.0) |
| Experiment Tracking | MLflow (>=2.15.0) |
| Structured Logging | structlog==24.4.0 |
| Async Queue | arq==0.26.3 + Redis (local dev / Docker Compose) |
| Storage | Postgres + SQLAlchemy async (local dev / Docker Compose) |
| Containerisation | Docker Compose |
| Language | Python 3.11 |

---

## Screenshots

### Hybrid Search Results
![Hybrid search results with relevance scores and source badges](docs/screenshot.png)

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

Or drive it from a browser instead of curl:

```bash
pip install -r requirements-ui.txt
streamlit run ui/streamlit_app.py
```

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

Postgres + Redis for the async service layer (`api/main.py`):

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
├── app/                            # Alternate single-process FastAPI app (LLM generation path)
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
│   ├── hybrid_search_service.py    # BM25 + FAISS + RRF + query rewriting + section-boost rerank
│   ├── bm25_service.py
│   ├── vector_service.py           # FAISS-backed async vector search
│   ├── corpus.py                   # Loads the real ingested corpus from data/processed/chunks.json
│   ├── query_rewrite.py            # Synonym-based query expansion
│   ├── rerank_service.py
│   └── parent_retrieval_service.py # Builds parent summaries dynamically from index_records.json
├── core/
│   ├── config.py                   # Pydantic settings from env
│   ├── security.py                 # Injection detection (8 patterns), PII redaction (email/phone/SSN/card)
│   ├── logging.py                  # structlog configuration
│   ├── tracing.py                  # traced_span: timed stage-logging (stage_timing log lines, not a real OTel tracer)
│   └── llm_factory.py              # LLM-as-judge: scores answer grounding via OpenAI or Anthropic
├── ingestion/                      # Document loading and chunking
│   ├── pipeline.py                 # Ingest raw docs → chunks with metadata inference
│   ├── chunker.py
│   └── connectors/local_files.py   # Loads .md files, doc_id = filename stem
├── schemas/                        # Pydantic request/response models
├── evals/
│   ├── dataset.json                # 60 labeled queries with expected_doc_ids
│   └── metrics.py                  # hit_rate_at_k, reciprocal_rank implementations
├── eval/
│   ├── ragas_runner.py             # 3-sample hit-rate benchmark (service layer)
│   └── mlflow_tracker.py           # MLflow wrapper for ragas_runner
├── scripts/
│   ├── run_ingestion.py            # Loads data/raw/ → data/processed/chunks.json
│   ├── build_index.py              # chunks.json → FAISS index + index_records.json
│   └── run_evals.py                # Full eval: Hit Rate@K, MRR, latency → MLflow
├── workers/
│   ├── tasks.py                    # arq task definitions (ingestion, eval)
│   └── settings.py                 # arq WorkerSettings with Redis connection
├── data/
│   ├── raw/                        # 40 source documents (incidents, runbooks, docs)
│   └── processed/                  # FAISS index, chunks.json, index_records.json
├── ui/
│   └── streamlit_app.py            # Thin Streamlit client for app/main.py's /query endpoint
├── tests/
├── docker/
├── docker-compose.yml              # Postgres + Redis for local dev
├── render.yaml                     # Legacy Render config (superseded by EC2 + Vercel)
├── Makefile
└── README.md
```

---

## CI/CD — GitHub Actions auto-deploy

Every push to `main` triggers a GitHub Actions pipeline:

1. Installs dependencies, runs ruff lint and two security scans (`requirements-ci.txt` and, separately, the exact `requirements-deploy.txt` that ships in the Docker image — audited independently since they carry different pins)
2. Builds the Docker image (one image, two entrypoints)
3. Runs the test suite (unit and security tests; integration tests require live services)
4. Opens SSH to the runner's own IP on the shared security group for the duration of the deploy, then deploys **both** services from that same image — `incidentmemai-api` (`api.main:app`, retrieval-only, port 8002) and `incidentmemai-app` (`app.main:app`, retrieval + LLM generation with citations, port 8003, what the Streamlit UI actually talks to) — each with its own health check and rollback, so a failure on one doesn't block the other from deploying
5. Revokes the runner's SSH access again in a cleanup step that runs even if the deploy failed

Required GitHub Secrets: `EC2_HOST`, `EC2_SSH_KEY`, `DEPLOY_AWS_ACCESS_KEY_ID`, `DEPLOY_AWS_SECRET_ACCESS_KEY`

## Why This Project

- **Retrieval architecture** beyond simple vector search — BM25 fusion, cross-encoder reranking, query rewriting, section-aware post-processing, all in a single coherent pipeline
- **Evaluation as a first-class concern** — labeled ground-truth dataset, Hit Rate@K and MRR computed against real retrieval, every run tracked with MLflow
- **Typed contracts and clear boundaries** — Pydantic schemas at every layer, clean service boundaries between retrieval, reranking, and generation
- **Two deployment patterns** — a lightweight single-process app (`app/`) and a full async microservice stack (`api/`) deployed via Docker on EC2 with a Next.js frontend on Vercel

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built by [Vamsi Krishna Sadu](https://github.com/vamsi513)
