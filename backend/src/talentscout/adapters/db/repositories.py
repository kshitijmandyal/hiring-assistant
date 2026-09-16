"""Postgres implementations of the repository protocols."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from talentscout.adapters.db.orm import (
    AssessmentRow,
    CandidateRow,
    InterviewRow,
    QuestionAssessmentRow,
    QuestionRow,
)
from talentscout.domain.assessment import Assessment
from talentscout.domain.candidate import Candidate
from talentscout.domain.interview import Interview
from talentscout.exceptions import (
    CandidateNotFoundError,
    DuplicateCandidateError,
    InterviewNotFoundError,
    StorageError,
)
from talentscout.mappers import assessment_mapper, candidate_mapper, interview_mapper

logger = logging.getLogger(__name__)


class PostgresCandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, candidate: Candidate) -> None:
        self._session.add(candidate_mapper.to_row(candidate))
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            # The unique index is the real guarantee; the service's pre-check only
            # makes the common case a friendlier error.
            raise DuplicateCandidateError("A candidate with this email already exists") from exc
        except SQLAlchemyError as exc:
            raise StorageError("Could not store candidate") from exc

    async def get(self, candidate_id: UUID) -> Candidate:
        row = await self._session.get(CandidateRow, candidate_id)
        if row is None:
            raise CandidateNotFoundError("No candidate with that id")
        return candidate_mapper.to_domain(row)

    async def find_by_email(self, email: str) -> Candidate | None:
        result = await self._session.execute(
            select(CandidateRow).where(CandidateRow.email == email.lower())
        )
        row = result.scalar_one_or_none()
        return candidate_mapper.to_domain(row) if row else None


class PostgresInterviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, interview: Interview) -> None:
        """Upsert the aggregate.

        Idempotent on interview id, so re-saving the same state does not accumulate
        rows the way the original in-memory submission list did.
        """
        try:
            row = await self._load_row(interview.id)
            if row is None:
                row = interview_mapper.to_interview_row(interview)
                row.questions = [
                    interview_mapper.to_question_row(q, interview_id=interview.id, position=i)
                    for i, q in enumerate(interview.questions)
                ]
                self._session.add(row)
            else:
                row.seniority = interview.seniority.value
                row.tech_stack = list(interview.tech_stack)
                row.status = interview.status.value
                row.finalised_at = interview.finalised_at
                self._append_new_questions(row, interview)

            await self._session.flush()
            self._sync_answers(row, interview)
            await self._session.flush()
        except SQLAlchemyError as exc:
            raise StorageError("Could not store interview") from exc

    @staticmethod
    def _append_new_questions(row: InterviewRow, interview: Interview) -> None:
        """Questions are immutable once generated, so only additions are possible."""
        known = {q.id for q in row.questions}
        for position, question in enumerate(interview.questions):
            if question.id not in known:
                row.questions.append(
                    interview_mapper.to_question_row(
                        question, interview_id=interview.id, position=position
                    )
                )

    @staticmethod
    def _sync_answers(row: InterviewRow, interview: Interview) -> None:
        for question_row in row.questions:
            answer = interview.answers.get(question_row.id)
            if answer is None:
                continue
            if question_row.answer is None:
                question_row.answer = interview_mapper.to_answer_row(answer)
            else:
                # Re-answering overwrites rather than inserting a second row.
                question_row.answer.text = answer.text
                question_row.answer.submitted_at = answer.submitted_at

    async def get(self, interview_id: UUID) -> Interview:
        row = await self._load_row(interview_id)
        if row is None:
            raise InterviewNotFoundError("No interview with that id")
        return interview_mapper.to_domain(row)

    async def list_for_candidate(self, candidate_id: UUID) -> list[Interview]:
        result = await self._session.execute(
            select(InterviewRow)
            .where(InterviewRow.candidate_id == candidate_id)
            .options(selectinload(InterviewRow.questions).selectinload(QuestionRow.answer))
            .order_by(InterviewRow.created_at.desc())
        )
        return [interview_mapper.to_domain(row) for row in result.scalars()]

    async def _load_row(self, interview_id: UUID) -> InterviewRow | None:
        result = await self._session.execute(
            select(InterviewRow)
            .where(InterviewRow.id == interview_id)
            .options(selectinload(InterviewRow.questions).selectinload(QuestionRow.answer))
        )
        return result.scalar_one_or_none()


class PostgresAssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, assessment: Assessment) -> None:
        try:
            self._session.add(assessment_mapper.to_row(assessment))
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            # The unique index on interview_id makes a double-finalise impossible at
            # the storage layer, not merely discouraged in the service.
            raise StorageError("This interview has already been assessed") from exc
        except SQLAlchemyError as exc:
            raise StorageError("Could not store assessment") from exc

    async def get_for_interview(self, interview_id: UUID) -> Assessment | None:
        result = await self._session.execute(
            select(AssessmentRow)
            .where(AssessmentRow.interview_id == interview_id)
            .options(
                selectinload(AssessmentRow.question_assessments).selectinload(
                    QuestionAssessmentRow.criterion_scores
                )
            )
        )
        row = result.scalar_one_or_none()
        return assessment_mapper.to_domain_assessment(row) if row else None
