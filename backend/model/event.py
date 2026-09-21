from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from model.award import Award


class Event(BaseModel):
    title: str | None = None
    description: str | None = None
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
