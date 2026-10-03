from typing import Literal
from pydantic import BaseModel, Field, field_validator
from validators import url


class Award(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    description: str | None = Field(default=None, min_length=5)
    number: int | Literal[""] | None = Field(default=None)
    cashValue: float | Literal[""] | None = Field(default=None)
    descriptionUrl: str | None = None
    titleImageUrl: str | None = None

    @field_validator("number")
    @classmethod
    def check_number(cls, value: int | Literal[""] | None) -> int | Literal[""] | None:
        if value not in (None, "") and value < 1:
            raise ValueError("must be at least 1")
        return value

    @field_validator("cashValue")
    @classmethod
    def check_cash_value(cls, value: float | Literal[""] | None) -> float | Literal[""] | None:
        if value not in (None, "") and value < 0:
            raise ValueError("must be non-negative")
        return value

    @field_validator("descriptionUrl", "titleImageUrl")
    @classmethod
    def check_url(cls, value: str | None) -> str | None:
        # empty string is allowed, the field is optional
        if value and not url(value):
            raise ValueError("must be a valid URL")
        return value
