from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class AgentResult(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
    attempts: int