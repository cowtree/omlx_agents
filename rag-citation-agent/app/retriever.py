from app.models import Document

class Retriever:

    def __init__(self, documents: list[Document]):
        self.documents = documents

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[Document]:
        """
        Retrieve the most relevant documents based on the query.
        This is a simple keyword-based retrieval for demonstration purposes.
        """
        # Simple keyword-based retrieval
        
        query_words = set(query.lower().split())

        scored_documents = []

        for document in self.documents:

            document_words = set(
                document.content.lower().split()
            )

            score = len(
                query_words.intersection(document_words)
            )

            scored_documents.append(
                (score, document)
            )

        scored_documents.sort(
            key=lambda item: item[0],
            reverse=True
        )
    
        return [
            document
            for score, document in scored_documents[:top_k]
            if score > 0
        ]