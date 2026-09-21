from pydantic import BaseModel, Field, field_validator
from validators import url


class Award(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    description: str | None = Field(default=None, min_length=5)
    number: int | None = Field(default=None, ge=1)
    cashValue: float | None = Field(default=None, ge=0)
    descriptionUrl: str | None = None
    titleImageUrl: str | None = None

    @field_validator("descriptionUrl", "titleImageUrl")
    @classmethod
    def check_url(cls, value: str | None) -> str | None:
        # empty string is allowed, the field is optional
        if value and not url(value):
            raise ValueError("must be a valid URL")
        return value
