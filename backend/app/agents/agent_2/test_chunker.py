
from backend.app.agents.agent_2.app.rag.document_loader import load_policy_documents
from backend.app.agents.agent_2.app.rag.chunker import chunk_documents


documents = load_policy_documents("policies")
chunks = chunk_documents(documents)

print(f"Documents loaded: {len(documents)}")
print(f"Chunks created: {len(chunks)}")

for chunk in chunks[:3]:
    print(f"\nChunk ID: {chunk.chunk_id}")
    print(f"Policy: {chunk.title}")
    print(f"Text preview: {chunk.text[:150]}")

