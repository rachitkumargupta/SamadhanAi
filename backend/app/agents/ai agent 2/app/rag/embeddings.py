
import voyageai

from app.config import settings


class EmbeddingService:
    """Generate text embeddings using the Voyage AI API."""

    def __init__(self) -> None:
        api_key = settings.voyage_api_key.strip()

        if not api_key:
            raise ValueError(
                "VOYAGE_API_KEY is missing from .env."
            )

        self.client = voyageai.Client(api_key=api_key)

    def embed(
        self,
        texts: list[str],
        model: str | None = None,
        input_type: str = "document",
    ) -> list[list[float]]:
        """Generate embeddings for documents or search queries."""

        if not texts:
            return []

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "Every text must be a non-empty string."
            )

        selected_model = (
            model or settings.embedding_model
        ).strip()

        if not selected_model:
            raise ValueError(
                "EMBEDDING_MODEL is not configured."
            )

        if input_type not in ("query", "document"):
            raise ValueError(
                "input_type must be 'query' or 'document'."
            )

        try:
            response = self.client.embed(
                texts=texts,
                model=selected_model,
                input_type=input_type,
            )

        except Exception as exc:
            # Show diagnostic details without printing credentials.
            print("\n--- Voyage AI Diagnostic ---")
            print("Error type:", type(exc).__name__)
            print("Error details:", str(exc))
            print("Model:", selected_model)
            print("Input type:", input_type)
            print("----------------------------\n")

            raise RuntimeError(
                "Voyage AI embedding request failed. "
                "Review the diagnostic output above."
            ) from exc

        embeddings = response.embeddings

        if len(embeddings) != len(texts):
            raise RuntimeError(
                "Voyage AI returned an unexpected number "
                "of embeddings."
            )

        if any(not vector for vector in embeddings):
            raise RuntimeError(
                "Voyage AI returned an empty embedding."
            )

        dimensions = {len(vector) for vector in embeddings}

        if len(dimensions) != 1:
            raise RuntimeError(
                "Embedding dimensions do not match."
            )

        return [
            [float(value) for value in vector]
            for vector in embeddings
        ]
