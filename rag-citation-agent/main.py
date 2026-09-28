from app.chunker import chunk_documents
from app.knowledge_base import DOCUMENTS
from app.retriever import Retriever


chunks = chunk_documents(
    DOCUMENTS,
    chunk_size=20,
    chunk_overlap=5,
)

retriever = Retriever(chunks)


question = "What is the company's parental leave policy?"

results = retriever.search(
    question,
    top_k=3,
    min_score=0.3
)


print(f"\nQuestion: {question}\n")


for result in results:

    print(f"Score: {result.score:.2f}")
    print(f"Chunk: {result.chunk.id}")
    print(f"Source: {result.chunk.source}")
    print(f"Content: {result.chunk.content}")
    print()