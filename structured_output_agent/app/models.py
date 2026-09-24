from typing import Literal

from pydantic import BaseModel, ValidationError

class ArticalAnalysis(BaseModel):
    title: str
    summary: str
    sentiment: Literal["positive", "negative", "neutral"]
