
from backend.app.agents.agent_2.app.rag.document_loader import load_policy_documents


documents = load_policy_documents("policies")

print(f"Documents loaded: {len(documents)}")

for document in documents:
    print(f"\nTitle: {document.title}")
    print(f"Source: {document.source}")
    print(f"Characters: {len(document.text)}")
