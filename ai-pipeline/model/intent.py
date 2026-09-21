from typing import Any, Literal, TypedDict


class Intent(TypedDict):
    path: str
    operation: Literal["add", "set", "remove", "submit"]
    value: Any
    error: str | None
