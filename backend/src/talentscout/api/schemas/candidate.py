"""Request and response bodies for candidate endpoints.

Separate from the domain models so the wire format can change independently, and so
a domain field is never exposed simply because it exists.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from talentscout.constants import YEARS_OF_EXPERIENCE_MAX


class CandidateCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=120, examples=["Ada Lovelace"])
    email: str = Field(examples=["ada@example.com"])
    phone: str = Field(examples=["+91 98765 43210"])
    years_of_experience: float = Field(ge=0, le=YEARS_OF_EXPERIENCE_MAX, examples=[6])
    desired_positions: list[str] = Field(min_length=1, max_length=5)
    location: str = Field(min_length=1, max_length=120, examples=["Pune, India"])


class CandidateResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str
    years_of_experience: float
    desired_positions: list[str]
    location: str
    seniority: str
    created_at: datetime
