-- Enables pgvector and creates the chunk-embedding table used by
-- retrieval/pgvector_store.py as an alternative to the FAISS index.
-- Runs automatically on first container start via docker-entrypoint-initdb.d.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    parent_id   TEXT,
    source      TEXT,
    title       TEXT,
    text        TEXT NOT NULL,
    section     TEXT,
    service     TEXT,
    severity    TEXT,
    tags        TEXT[] DEFAULT '{}',
    path        TEXT,
    url         TEXT,
    -- all-MiniLM-L6-v2 produces 384-dim embeddings; fixed to match the
    -- embedder actually in use (retrieval/embedder.py), not a placeholder.
    embedding   VECTOR(384) NOT NULL
);

-- Exact cosine search is realistic at this corpus size (tens of documents,
-- hundreds of chunks) -- an ivfflat/hnsw approximate index would add
-- tuning complexity with no real benefit until the corpus is orders of
-- magnitude larger, so none is created here.
CREATE INDEX IF NOT EXISTS document_chunks_doc_id_idx ON document_chunks (doc_id);
