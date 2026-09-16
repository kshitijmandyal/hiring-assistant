from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MAX_QUESTION_SCORE = 10


class Recommendation(StrEnum):
    STRONG_PROCEED = "strong_proceed"
    PROCEED = "proceed"
    BORDERLINE = "borderline"
    DO_NOT_PROCEED = "do_not_proceed"


class CriterionScore(BaseModel):
    """One rubric criterion, judged against the candidate's actual answer."""

    model_config = ConfigDict(frozen=True)

    criterion: str
    met: bool
    justification: str = Field(min_length=1, max_length=500)


class QuestionAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    question_id: UUID
    score: int = Field(ge=0, le=MAX_QUESTION_SCORE)
    criterion_scores: list[CriterionScore]
    strengths: list[str] = Field(default_factory=list, max_length=5)
    gaps: list[str] = Field(default_factory=list, max_length=5)
    # Non-empty when a guardrail adjusted or distrusted this grade. Surfaced to the
    # interviewer rather than hidden, since it is a reason to read the answer manually.
    guardrail_flags: list[str] = Field(default_factory=list)

    @property
    def is_trustworthy(self) -> bool:
        return not self.guardrail_flags


class Assessment(BaseModel):
    """The graded outcome of an interview.

    Coverage is reported separately from score rather than folded into it: the previous
    implementation divided by the full question count, so skipping questions looked
    identical to answering them badly.
    """

    model_config = ConfigDict(frozen=True)

    interview_id: UUID
    question_assessments: list[QuestionAssessment] = Field(min_length=1)
    questions_total: int = Field(gt=0)
    summary: str = Field(min_length=1, max_length=2_000)
    recommendation: Recommendation
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def questions_answered(self) -> int:
        return len(self.question_assessments)

    @property
    def coverage(self) -> float:
        """Share of questions the candidate attempted, 0.0-1.0."""
        return self.questions_answered / self.questions_total

    @property
    def average_score(self) -> float:
        """Mean score across answered questions only."""
        return sum(qa.score for qa in self.question_assessments) / self.questions_answered

    @property
    def score_percentage(self) -> float:
        return self.average_score / MAX_QUESTION_SCORE * 100
