from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Uniform error body. Clients branch on `code`, never on `message`."""

    code: str = Field(examples=["CANDIDATE_NOT_FOUND"])
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
