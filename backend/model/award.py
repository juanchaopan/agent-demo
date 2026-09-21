from pydantic import BaseModel


class Award(BaseModel):
    title: str | None = None
    description: str | None = None
    number: int | None = None
    cashValue: float | None = None
    descriptionUrl: str | None = None
    titleImageUrl: str | None = None
