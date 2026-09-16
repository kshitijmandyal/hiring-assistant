from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from talentscout.constants.auth import Role
from talentscout.domain.value_objects import Email, FullName


class User(BaseModel):
    """An interviewer. Candidates are not users — they hold a scoped invite token."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    email: Email
    full_name: FullName
    # Never the password itself. The domain never sees a plaintext password beyond
    # the moment it is hashed at the boundary.
    password_hash: str
    role: Role = Role.INTERVIEWER
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Principal(BaseModel):
    """Who is making the current request, resolved from a bearer token."""

    model_config = ConfigDict(frozen=True)

    subject_id: UUID
    role: Role
    # Set only for candidate tokens: the one interview this principal may touch.
    interview_id: UUID | None = None

    @property
    def is_interviewer(self) -> bool:
        return self.role is Role.INTERVIEWER

    def may_access_interview(self, interview_id: UUID) -> bool:
        if self.is_interviewer:
            return True
        return self.interview_id == interview_id
