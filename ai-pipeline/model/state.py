from typing import TypedDict
from langchain_core.messages import AnyMessage
from model.event import Event
from model.intent import Intent


class State(TypedDict):
    messages: list[AnyMessage]
    event: Event
    request: str | None
    intents: list[Intent] | None
    response: str | None
