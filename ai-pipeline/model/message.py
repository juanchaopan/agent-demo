from typing import Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str = Field(alias="_id")
    status: Literal["pending", "processed", "failed"]
    role: Literal["user", "assistant"]
    content: str | None
