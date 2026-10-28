
from typing import Any
from pgvector.psycopg import register_vector
import psycopg
from psycopg.rows import dict_row


class VectorStore:
    """Store and retrieve policy embeddings using PostgreSQL and pgvector."""

    def __init__(self, database_url: str) -> None:
        if not database_url or not database_url.strip():
            raise ValueError(
                "DATABASE_URL is not configured. "
                "Obtain the PostgreSQL connection URL before connecting."
            )

        self.database_url = database_url.strip()

    def _connect(self) -> psycopg.Connection:
        connection = psycopg.connect(
            self.database_url,
            row_factory=dict_row,
            connect_timeout=10,
        )
        register_vector(connection)
        return connection

    def initialize(self, dimensions: int) -> None:
        """Create the policy vector table for the selected embedding dimensions."""
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive.")

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS policy_chunks (
                        id BIGSERIAL PRIMARY KEY,
                        policy_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source TEXT NOT NULL,
                        document_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                        chunk_index INTEGER NOT NULL,
                        embedding VECTOR({dimensions}) NOT NULL,
                        UNIQUE (policy_id, chunk_index)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    policy_chunks_policy_id_idx
                    ON policy_chunks (policy_id)
                    """
                )
            connection.commit()

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Insert or update policy chunks and their embeddings."""
        if not chunks:
            return 0

        query = """
            INSERT INTO policy_chunks (
                policy_id,
                title,
                content,
                source,
                document_status,
                chunk_index,
                embedding
            )
            VALUES (
                %(policy_id)s,
                %(title)s,
                %(content)s,
                %(source)s,
                %(document_status)s,
                %(chunk_index)s,
                %(embedding)s
            )
            ON CONFLICT (policy_id, chunk_index)
            DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                source = EXCLUDED.source,
                document_status = EXCLUDED.document_status,
                embedding = EXCLUDED.embedding
        """

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(query, chunks)
            connection.commit()

        return len(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find policy chunks closest to the query embedding."""
        if not query_embedding:
            raise ValueError("Query embedding must not be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query = """
            SELECT
                policy_id,
                title,
                content,
                source,
                document_status,
                chunk_index,
                embedding <=> %s AS distance
            FROM policy_chunks
            ORDER BY embedding <=> %s
            LIMIT %s
        """

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (query_embedding, query_embedding, top_k),
                )
                return list(cursor.fetchall())
