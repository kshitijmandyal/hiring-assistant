"""Protocols the services depend on.

These are the dependency-inversion seams: services import these, never a concrete
adapter, so swapping Claude for another provider or Postgres for another store is
a change confined to adapters/.
"""

from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from talentscout.domain.assessment import Assessment, QuestionAssessment
from talentscout.domain.candidate import Candidate
from talentscout.domain.enums import SeniorityLevel
from talentscout.domain.interview import Answer, Interview, Question
from talentscout.domain.user import User


@runtime_checkable
class QuestionGenerator(Protocol):
    async def generate(
        self,
        *,
        technology: str,
        seniority: SeniorityLevel,
        count: int,
    ) -> list[Question]:
        """Produce `count` questions for one technology, each carrying its own rubric.

        Raises QuestionGenerationError if the provider returns nothing usable.
        """
        ...


@runtime_checkable
class AnswerGrader(Protocol):
    async def grade(
        self,
        *,
        question: Question,
        answer: Answer,
        seniority: SeniorityLevel,
    ) -> QuestionAssessment:
        """Judge one answer against its question's rubric.

        Raises GradingError if the provider returns nothing usable.
        """
        ...


@runtime_checkable
class AssessmentSummariser(Protocol):
    async def summarise(
        self,
        *,
        interview: Interview,
        question_assessments: list[QuestionAssessment],
    ) -> tuple[str, str]:
        """Return (summary, recommendation value) for a fully graded interview."""
        ...


@runtime_checkable
class CandidateRepository(Protocol):
    async def add(self, candidate: Candidate) -> None:
        """Raises DuplicateCandidateError if the email is already registered."""
        ...

    async def get(self, candidate_id: UUID) -> Candidate:
        """Raises CandidateNotFoundError if absent."""
        ...

    async def find_by_email(self, email: str) -> Candidate | None: ...


@runtime_checkable
class InterviewRepository(Protocol):
    async def save(self, interview: Interview) -> None:
        """Insert or update. Idempotent on interview id."""
        ...

    async def get(self, interview_id: UUID) -> Interview:
        """Raises InterviewNotFoundError if absent."""
        ...

    async def list_for_candidate(self, candidate_id: UUID) -> list[Interview]: ...

    async def lock(self, interview_id: UUID) -> None:
        """Holds the interview for the rest of the transaction; concurrent lockers wait."""
        ...


@runtime_checkable
class AssessmentRepository(Protocol):
    async def save(self, assessment: Assessment) -> None: ...

    async def get_for_interview(self, interview_id: UUID) -> Assessment | None: ...


# --- Authentication ---------------------------------------------------------


@runtime_checkable
class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Raises WeakPasswordError if the password fails policy."""
        ...

    def verify(self, password: str, password_hash: str) -> bool: ...


@runtime_checkable
class TokenIssuer(Protocol):
    def issue_access_token(self, *, user_id: UUID) -> str: ...

    def issue_refresh_token(self, *, user_id: UUID) -> tuple[str, str, datetime]:
        """Returns (token, jti, expires_at)."""
        ...

    def issue_invite_token(self, *, candidate_id: UUID, interview_id: UUID) -> str: ...

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """Raises TokenExpiredError or TokenInvalidError."""
        ...


@runtime_checkable
class UserRepository(Protocol):
    async def add(self, user: User) -> None:
        """Raises EmailAlreadyRegisteredError if the email is taken."""
        ...

    async def find_by_email(self, email: str) -> User | None: ...

    async def get(self, user_id: UUID) -> User | None: ...


@runtime_checkable
class RefreshTokenRepository(Protocol):
    async def store(self, *, user_id: UUID, jti: str, expires_at: datetime) -> None: ...

    async def is_active(self, jti: str) -> bool: ...

    async def revoke(self, jti: str) -> None: ...
