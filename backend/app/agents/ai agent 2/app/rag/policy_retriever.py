
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.rag.chunker import PolicyChunk


class PolicyRetriever:

    def __init__(self, chunks: list[PolicyChunk]):
        self.chunks = chunks

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            stop_words="english",
        )

        self.matrix = (
            self.vectorizer.fit_transform(
                [chunk.text for chunk in chunks]
            )
            if chunks
            else None
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Retrieve relevant chunks and preserve their provenance."""

        if not query.strip() or not self.chunks:
            return []

        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            self.matrix,
        ).flatten()

        ranked_indices = scores.argsort()[::-1][:top_k]

        results = []

        for index in ranked_indices:
            score = float(scores[index])

            if score <= 0:
                continue

            chunk = self.chunks[index]

            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "policy_id": chunk.policy_id,
                    "title": chunk.title,
                    "source": chunk.source,
                    "excerpt": chunk.text,
                    "document_status": chunk.status,
                    "relevance_score": round(score, 4),
                }
            )

        return results
