
from backend.app.agents.agent_2.app.rag.document_loader import PolicyDocument
from backend.app.agents.agent_2.app.rag.chunker import chunk_documents
from backend.app.agents.agent_2.app.rag.policy_retriever import PolicyRetriever


# Temporary test data only — NOT an official municipal policy.
sample_document = PolicyDocument(
    policy_id="SAMPLE-001",
    title="Sample Water and Electrical Safety Notes",
    source="test_fixture_only",
    text=(
        "Water leakage on public roads should be reported "
        "for assessment by the relevant water supply authority. "
        "An exposed electrical wire may present an immediate "
        "safety hazard and should be reported to the responsible "
        "electricity authority for urgent assessment."
    ),
)

chunks = chunk_documents([sample_document])
retriever = PolicyRetriever(chunks)

results = retriever.retrieve(
    "exposed electrical wire safety hazard",
    top_k=3,
)

print(f"Chunks indexed: {len(chunks)}")
print(f"Results found: {len(results)}")

for result in results:
    print(f"\nTitle: {result['title']}")
    print(f"Relevance: {result['relevance_score']}")
    print(f"Excerpt: {result['excerpt']}")
    print(f"Source: {result['source']}")
