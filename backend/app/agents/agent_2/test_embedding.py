
from backend.app.agents.agent_2.app.config import settings
from backend.app.agents.agent_2.app.rag.embeddings import EmbeddingService


def main() -> None:
    if not settings.voyage_api_key.strip():
        raise RuntimeError(
            "VOYAGE_API_KEY is empty. Check your .env file."
        )

    print("Voyage API key loaded: True")
    print("Embedding model:", settings.embedding_model)

    service = EmbeddingService()

    # Test policy-document embeddings.
    documents = [
        "The water department handles pipeline leakage.",
        "Exposed electrical wires create a safety hazard.",
    ]

    document_embeddings = service.embed(
        texts=documents,
        input_type="document",
    )

    # Test complaint-query embeddings.
    query_embeddings = service.embed(
        texts=["There is a leaking water pipeline."],
        input_type="query",
    )

    print("\nEmbedding test successful.")
    print("Document vectors:", len(document_embeddings))
    print("Query vectors:", len(query_embeddings))
    print("Vector dimensions:", len(document_embeddings[0]))
    print("Query dimensions:", len(query_embeddings[0]))

    assert (
        len(document_embeddings[0])
        == len(query_embeddings[0])
    ), "Document and query embedding dimensions differ."

    print("Document/query dimensions match.")


if __name__ == "__main__":
    main()
