from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from talentscout.constants.auth import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str


class InviteResponse(BaseModel):
    """Handed to the interviewer, who passes the link to the candidate."""

    interview_id: UUID
    invite_token: str
    expires_in_days: int
