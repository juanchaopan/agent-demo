from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from validators import url
from model.award import Award

# (earlier, later, later may equal earlier)
DATE_ORDER = [
    ("openRegistrationDate", "closeRegistrationDate", False),
    ("closeRegistrationDate", "openSubmissionDate", True),
    ("openSubmissionDate", "closeSubmissionDate", False),
    ("closeSubmissionDate", "openFinalizeDate", True),
    ("openFinalizeDate", "closeFinalizeDate", False),
]


class Event(BaseModel):
    title: str | None = Field(default=None, min_length=4)
    description: str | None = Field(default=None, min_length=10)
    openRegistrationDate: datetime | None = None
    closeRegistrationDate: datetime | None = None
    openSubmissionDate: datetime | None = None
    closeSubmissionDate: datetime | None = None
    openFinalizeDate: datetime | None = None
    closeFinalizeDate: datetime | None = None
    bannerImageUrl: str | None = None
    videoUrl: str | None = None
    registrationFormUrl: str | None = None
    submissionFormUrl: str | None = None
    awards: list[Award] | None = None
    editStatus: Literal["draft", "published", "archived"] | None = None

    @field_validator(
        "bannerImageUrl", "videoUrl", "registrationFormUrl", "submissionFormUrl"
    )
    @classmethod
    def check_url(cls, value: str | None) -> str | None:
        # empty string is allowed, the field is optional
        if value and not url(value):
            raise ValueError("must be a valid URL")
        return value

    @model_validator(mode="after")
    def check_dates(self):
        for earlier, later, allow_equal in DATE_ORDER:
            a, b = getattr(self, earlier), getattr(self, later)
            if a is not None and b is not None and (a > b or (a == b and not allow_equal)):
                raise ValueError(f"{later} must be after {earlier}")
        return self
