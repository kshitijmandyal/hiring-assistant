"""Screening use cases: register a candidate, generate their questions, record answers."""

import asyncio
import logging
from uuid import UUID

from talentscout.constants import (
    QUESTIONS_PER_TECHNOLOGY,
    QUESTIONS_PER_TECHNOLOGY_MAX,
    QUESTIONS_PER_TECHNOLOGY_MIN,
)
from talentscout.domain.candidate import Candidate
from talentscout.domain.interview import Answer, Interview
from talentscout.exceptions import DuplicateCandidateError, ValidationError
from talentscout.interfaces import (
    CandidateRepository,
    InterviewRepository,
    QuestionGenerator,
)

logger = logging.getLogger(__name__)


class ScreeningService:
    def __init__(
        self,
        *,
        candidates: CandidateRepository,
        interviews: InterviewRepository,
        question_generator: QuestionGenerator,
    ) -> None:
        self._candidates = candidates
        self._interviews = interviews
        self._question_generator = question_generator

    async def register_candidate(self, candidate: Candidate) -> Candidate:
        if await self._candidates.find_by_email(candidate.email) is not None:
            raise DuplicateCandidateError("A candidate with this email is already registered")

        await self._candidates.add(candidate)
        logger.info("Candidate registered", extra={"seniority": candidate.seniority})
        return candidate

    async def start_interview(
        self,
        *,
        candidate_id: UUID,
        tech_stack: list[str],
        questions_per_technology: int = QUESTIONS_PER_TECHNOLOGY,
    ) -> Interview:
        if not (
            QUESTIONS_PER_TECHNOLOGY_MIN <= questions_per_technology <= QUESTIONS_PER_TECHNOLOGY_MAX
        ):
            raise ValidationError(
                f"questions_per_technology must be between {QUESTIONS_PER_TECHNOLOGY_MIN} "
                f"and {QUESTIONS_PER_TECHNOLOGY_MAX}"
            )

        candidate = await self._candidates.get(candidate_id)
        interview = Interview(
            candidate_id=candidate.id,
            seniority=candidate.seniority,
            tech_stack=tech_stack,
        )

        # Technologies are independent, so generate concurrently rather than serially
        # as the original did — this is the bulk of the request's latency.
        results = await asyncio.gather(
            *(
                self._question_generator.generate(
                    technology=technology,
                    seniority=interview.seniority,
                    count=questions_per_technology,
                )
                for technology in interview.tech_stack
            )
        )

        questions = [question for batch in results for question in batch]
        interview = interview.with_questions(questions)
        await self._interviews.save(interview)

        logger.info(
            "Interview started with %d questions across %d technologies",
            len(questions),
            len(interview.tech_stack),
            extra={"seniority": interview.seniority},
        )
        return interview

    async def record_answer(self, *, interview_id: UUID, answer: Answer) -> Interview:
        interview = await self._interviews.get(interview_id)
        updated = interview.with_answer(answer)
        await self._interviews.save(updated)

        logger.info(
            "Answer recorded (%d of %d)",
            updated.answered_count,
            len(updated.questions),
        )
        return updated

    async def get_interview(self, interview_id: UUID) -> Interview:
        return await self._interviews.get(interview_id)

    async def get_candidate(self, candidate_id: UUID) -> Candidate:
        return await self._candidates.get(candidate_id)
