
from typing import Any

from app.config import settings
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore


class PgVectorRetriever:
    """Index policy chunks and retrieve them using vector similarity."""

    def __init__(self) -> None:
        if not settings.database_url:
            raise ValueError(
                "DATABASE_URL is not configured. "
                "Use RETRIEVAL_BACKEND=tfidf until the database is available."
            )

        if not settings.embedding_model.strip():
            raise ValueError(
                "EMBEDDING_MODEL is not configured."
            )

        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(settings.database_url)
        self.embedding_model = settings.embedding_model.strip()

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using the configured Ollama model."""
        return self.embedding_service.embed(
            texts=texts,
            model=self.embedding_model,
        )

    def index_chunks(self, chunks: list[Any]) -> int:
        """Embed and save policy chunks to PostgreSQL."""
        if not chunks:
            return 0

        texts = [chunk.text for chunk in chunks]
        embeddings = self._embed(texts)

        dimensions = len(embeddings[0])
        if dimensions == 0 or any(
            len(vector) != dimensions for vector in embeddings
        ):
            raise ValueError("Embedding dimensions are inconsistent.")

        self.vector_store.initialize(dimensions)

        records = []
        for chunk, embedding in zip(chunks, embeddings):
            records.append(
                {
                    "policy_id": chunk.policy_id,
                    "title": chunk.title,
                    "content": chunk.text,
                    "source": chunk.source,
                    "document_status": chunk.status,
                    "chunk_index": self._get_chunk_index(chunk),
                    "embedding": embedding,
                }
            )

        return self.vector_store.upsert_chunks(records)

    @staticmethod
    def _get_chunk_index(chunk: Any) -> int:
        """Obtain a stable chunk index from the existing chunk object."""
        chunk_id = str(chunk.chunk_id)

        if chunk_id.isdigit():
            return int(chunk_id)

        suffix = chunk_id.rsplit("-", 1)[-1]
        if suffix.isdigit():
            return int(suffix)

        raise ValueError(
            f"Cannot determine numeric chunk index from {chunk_id!r}."
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve semantically similar policy chunks."""
        if not query.strip():
            return []

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_embedding = self._embed([query])[0]
        matches = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        results = []
        for match in matches:
            distance = float(match["distance"])

            results.append(
                {
                    "policy_id": match["policy_id"],
                    "title": match["title"],
                    "source": match["source"],
                    "excerpt": match["content"],
                    "document_status": match["document_status"],
                    "relevance_score": round(
                        max(0.0, 1.0 - distance), 4
                    ),
                }
            )

        return results
