from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from talentscout.constants import (
    ANSWER_MAX_LENGTH,
    ANSWER_MIN_LENGTH,
    QUESTIONS_PER_TECHNOLOGY,
    QUESTIONS_PER_TECHNOLOGY_MAX,
    QUESTIONS_PER_TECHNOLOGY_MIN,
    TECH_STACK_MAX_SIZE,
)


class InterviewStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tech_stack: list[str] = Field(
        min_length=1,
        max_length=TECH_STACK_MAX_SIZE,
        examples=[["Python", "PostgreSQL", "React"]],
    )
    questions_per_technology: int = Field(
        default=QUESTIONS_PER_TECHNOLOGY,
        ge=QUESTIONS_PER_TECHNOLOGY_MIN,
        le=QUESTIONS_PER_TECHNOLOGY_MAX,
    )


class AnswerSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: UUID
    text: str = Field(min_length=ANSWER_MIN_LENGTH, max_length=ANSWER_MAX_LENGTH)


class QuestionResponse(BaseModel):
    id: UUID
    technology: str
    prompt: str
    kind: str
    # The rubric is deliberately absent: it is the answer key, and the candidate
    # fetches this same payload.


class InterviewResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    seniority: str
    tech_stack: list[str]
    status: str
    questions: list[QuestionResponse]
    answered_question_ids: list[UUID]
    created_at: datetime
    finalised_at: datetime | None
