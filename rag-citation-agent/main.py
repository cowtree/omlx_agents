from app.knowledge_base import DOCUMENTS
from app.retriever import Retriever

retriever = Retriever(DOCUMENTS)

question = "How many vacation days do employees receive?"

results = retriever.search(
    question,
    top_k = 3
)

print(f"\nQuestion: {question}\n")

for document in results:

    print(f"Title: {document.title}")
    print(f"Source: {document.source}")
    print(f"Content:{document.content}")
    print()