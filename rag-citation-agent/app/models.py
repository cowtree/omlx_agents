from pydantic import BaseModel, Field

class Document(BaseModel):

    id: str

    title: str

    content: str

    source: str

