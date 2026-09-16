from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from talentscout.domain.enums import SeniorityLevel
from talentscout.domain.value_objects import (
    DesiredPosition,
    Email,
    FullName,
    Location,
    PhoneNumber,
    YearsOfExperience,
)


class Candidate(BaseModel):
    """A person being screened.

    Frozen: a correction is a new record, which keeps assessments traceable to the
    exact details they were produced against.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    full_name: FullName
    email: Email
    phone: PhoneNumber
    years_of_experience: YearsOfExperience
    desired_positions: list[DesiredPosition] = Field(min_length=1, max_length=5)
    location: Location
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def seniority(self) -> SeniorityLevel:
        return SeniorityLevel.from_years(self.years_of_experience)
