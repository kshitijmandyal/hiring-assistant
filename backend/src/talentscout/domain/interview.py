from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from talentscout.constants import TECH_STACK_MAX_SIZE
from talentscout.domain.enums import InterviewStatus, QuestionKind, SeniorityLevel
from talentscout.domain.value_objects import (
    AnswerText,
    TechnologyName,
    deduplicate_technologies,
)
from talentscout.exceptions import (
    InterviewAlreadyFinalisedError,
    InterviewNotReadyError,
    QuestionNotFoundError,
)

TechStack = Annotated[
    list[TechnologyName],
    Field(min_length=1, max_length=TECH_STACK_MAX_SIZE),
    AfterValidator(deduplicate_technologies),
]


class Question(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    technology: TechnologyName
    prompt: str = Field(min_length=10, max_length=1_000)
    kind: QuestionKind
    # What a strong answer contains. Generated with the question and reused verbatim
    # when grading, so the candidate is measured against a stated standard.
    rubric: list[str] = Field(min_length=1, max_length=6)


class Answer(BaseModel):
    model_config = ConfigDict(frozen=True)

    question_id: UUID
    text: AnswerText
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Interview(BaseModel):
    """Aggregate root. Owns the question set and the answers given to it."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    seniority: SeniorityLevel
    tech_stack: TechStack
    questions: list[Question] = Field(default_factory=list)
    answers: dict[UUID, Answer] = Field(default_factory=dict)
    status: InterviewStatus = InterviewStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finalised_at: datetime | None = None

    @property
    def answered_count(self) -> int:
        return len(self.answers)

    @property
    def is_finalised(self) -> bool:
        return self.status is InterviewStatus.FINALISED

    def questions_for(self, technology: str) -> list[Question]:
        key = technology.casefold()
        return [q for q in self.questions if q.technology.casefold() == key]

    def with_questions(self, questions: list[Question]) -> "Interview":
        self._reject_if_finalised()
        return self.model_copy(
            update={"questions": questions, "status": InterviewStatus.QUESTIONS_READY}
        )

    def with_answer(self, answer: Answer) -> "Interview":
        self._reject_if_finalised()
        if not any(q.id == answer.question_id for q in self.questions):
            raise QuestionNotFoundError(
                "Answer does not correspond to any question in this interview"
            )
        return self.model_copy(
            update={
                "answers": {**self.answers, answer.question_id: answer},
                "status": InterviewStatus.IN_PROGRESS,
            }
        )

    def finalised(self) -> "Interview":
        self._reject_if_finalised()
        if not self.answers:
            raise InterviewNotReadyError("Cannot finalise an interview with no answers")
        return self.model_copy(
            update={
                "status": InterviewStatus.FINALISED,
                "finalised_at": datetime.now(UTC),
            }
        )

    def _reject_if_finalised(self) -> None:
        if self.is_finalised:
            raise InterviewAlreadyFinalisedError("This interview has already been finalised")
