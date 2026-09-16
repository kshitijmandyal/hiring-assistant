"""Response schemas for constrained decoding.

Deliberately separate from the domain models: these mirror what the model is asked
to emit, and mappers translate them inwards. Keeping them apart means a prompt change
cannot quietly reshape the domain.
"""

from pydantic import BaseModel, Field

from talentscout.constants import QUESTIONS_PER_TECHNOLOGY_MAX
from talentscout.domain.assessment import MAX_QUESTION_SCORE
from talentscout.domain.enums import QuestionKind


class LLMQuestion(BaseModel):
    prompt: str = Field(description="The interview question, as it will be shown to the candidate")
    kind: QuestionKind
    rubric: list[str] = Field(
        description="2-4 specific things a strong answer contains",
        min_length=1,
        max_length=6,
    )


class LLMQuestionSet(BaseModel):
    questions: list[LLMQuestion] = Field(min_length=1, max_length=QUESTIONS_PER_TECHNOLOGY_MAX)


class LLMCriterionScore(BaseModel):
    criterion: str = Field(description="The rubric criterion, copied verbatim")
    met: bool
    justification: str = Field(description="One sentence citing the candidate's actual words")


class LLMGrade(BaseModel):
    criterion_scores: list[LLMCriterionScore]
    score: int = Field(ge=0, le=MAX_QUESTION_SCORE)
    strengths: list[str] = Field(default_factory=list, max_length=5)
    gaps: list[str] = Field(default_factory=list, max_length=5)


class LLMSummary(BaseModel):
    summary: str = Field(description="2-4 sentences for the hiring manager")
    recommendation: str = Field(
        description="One of: strong_proceed, proceed, borderline, do_not_proceed"
    )
