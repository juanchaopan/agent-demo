from pydantic import BaseModel, Field
from model.event import Event
from model.message import Message


class Conversation(BaseModel):
    id: str = Field(alias="_id")
    messages: list[Message]
    event: Event
