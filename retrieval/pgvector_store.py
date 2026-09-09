import psycopg
from pgvector.psycopg import register_vector

from core.config import settings

# Sync psycopg, matching the sync shape of FaissStore/BM25Store used by the
# rest of retrieval/pipeline.py -- core/db.py's asyncpg engine is for the
# FastAPI app's own request path, not these offline ingestion/eval scripts.
_SYNC_DSN = settings.postgres_dsn.replace("postgresql+asyncpg://", "postgresql://")


class PgVectorStore:
    def __init__(self) -> None:
        self.conn = psycopg.connect(_SYNC_DSN, autocommit=True)
        register_vector(self.conn)

    def add(self, embeddings: list[list[float]], records: list[dict]) -> None:
        with self.conn.cursor() as cur:
            for embedding, record in zip(embeddings, records):
                cur.execute(
                    """
                    INSERT INTO document_chunks
                        (chunk_id, doc_id, parent_id, source, title, text,
                         section, service, severity, tags, path, url, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        doc_id = EXCLUDED.doc_id,
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        record["chunk_id"],
                        record["doc_id"],
                        record.get("parent_id"),
                        record.get("source"),
                        record.get("title"),
                        record["text"],
                        record.get("section"),
                        record.get("service"),
                        record.get("severity"),
                        record.get("tags") or [],
                        record.get("path"),
                        record.get("url"),
                        embedding,
                    ),
                )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        # Embeddings are L2-normalized at encode time (see retrieval/embedder.py),
        # so cosine distance and negative inner product rank identically;
        # cosine (<=>) is used for readability. Converted to a similarity
        # score (1 - distance) so callers see the same "higher is better"
        # convention as FaissStore's vector_score.
        with self.conn.cursor() as cur:
            # Postgres can't infer a bare parameter's type in a standalone
            # `<=>` expression (no target column to infer from, unlike an
            # INSERT ... VALUES), so it defaults to double precision[] and
            # the operator lookup fails -- explicit ::vector casts fix this.
            cur.execute(
                """
                SELECT chunk_id, doc_id, parent_id, source, title, text,
                       section, service, severity, tags, path, url,
                       1 - (embedding <=> %s::vector) AS vector_score
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (query_embedding, query_embedding, top_k),
            )
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def count(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM document_chunks")
            return cur.fetchone()[0]

    def clear(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE document_chunks")

    def close(self) -> None:
        self.conn.close()
