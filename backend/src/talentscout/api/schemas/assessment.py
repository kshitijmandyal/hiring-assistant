from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CriterionScoreResponse(BaseModel):
    criterion: str
    met: bool
    justification: str


class QuestionAssessmentResponse(BaseModel):
    question_id: UUID
    score: int
    criterion_scores: list[CriterionScoreResponse]
    strengths: list[str]
    gaps: list[str]
    # Non-empty when a guardrail adjusted this grade. Exposed rather than hidden so
    # the interviewer knows to read the answer themselves.
    guardrail_flags: list[str]


class AssessmentResponse(BaseModel):
    interview_id: UUID
    question_assessments: list[QuestionAssessmentResponse]
    questions_answered: int
    questions_total: int
    coverage: float
    average_score: float
    score_percentage: float
    summary: str
    recommendation: str
    assessed_at: datetime
