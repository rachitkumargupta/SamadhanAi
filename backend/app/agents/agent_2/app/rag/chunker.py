
from dataclasses import dataclass

from .document_loader import PolicyDocument


@dataclass
class PolicyChunk:
    chunk_id: str
    policy_id: str
    title: str
    source: str
    text: str
    status: str = "UNVERIFIED"


def chunk_documents(
    documents: list[PolicyDocument],
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[PolicyChunk]:
    """Split policy documents while preserving their metadata."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and less than chunk_size."
        )

    chunks: list[PolicyChunk] = []
    step = chunk_size - overlap

    for document in documents:
        text = document.text.strip()

        if not text:
            continue

        for start in range(0, len(text), step):
            excerpt = text[start:start + chunk_size].strip()

            if not excerpt:
                continue

            chunks.append(
                PolicyChunk(
                    chunk_id=f"{document.policy_id}-{start}",
                    policy_id=document.policy_id,
                    title=document.title,
                    source=document.source,
                    text=excerpt,
                    status=document.status,
                )
            )

            if start + chunk_size >= len(text):
                break

    return chunks
