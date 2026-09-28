from app.models import Chunk, Document


def chunk_document(
    document: Document,
    chunk_size: int = 100,
    chunk_overlap: int = 20,
) -> list[Chunk]:

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    words = document.content.split()

    chunks = []

    step = chunk_size - chunk_overlap

    for index, start in enumerate(
        range(0, len(words), step)
    ):
        chunk_words = words[start:start + chunk_size]

        if not chunk_words:
            break

        content = " ".join(chunk_words)

        chunks.append(
            Chunk(
                id=f"{document.id}-chunk-{index}",
                document_id=document.id,
                content=content,
                source=document.source,
                chunk_index=index,
            )
        )

    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 100,
    chunk_overlap: int = 20,
) -> list[Chunk]:

    chunks = []

    for document in documents:

        document_chunks = chunk_document(
            document=document,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        chunks.extend(document_chunks)

    return chunks