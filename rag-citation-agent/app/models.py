from pydantic import BaseModel, Field

class Document(BaseModel):

    id: str
    title: str
    content: str
    source: str


class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    source: str
    chunk_index: int


class RetrievalResult(BaseModel):
    chunk: Chunk
    score: float

