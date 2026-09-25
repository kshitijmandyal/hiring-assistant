"""Finalises an interview and produces its graded assessment."""

import asyncio
import logging
from uuid import UUID

from talentscout.domain.assessment import Assessment, Recommendation
from talentscout.exceptions import InterviewNotReadyError
from talentscout.interfaces import (
    AnswerGrader,
    AssessmentRepository,
    AssessmentSummariser,
    InterviewRepository,
)

logger = logging.getLogger(__name__)


class AssessmentService:
    def __init__(
        self,
        *,
        interviews: InterviewRepository,
        assessments: AssessmentRepository,
        grader: AnswerGrader,
        summariser: AssessmentSummariser,
    ) -> None:
        self._interviews = interviews
        self._assessments = assessments
        self._grader = grader
        self._summariser = summariser

    async def finalise(self, interview_id: UUID) -> Assessment:
        # A double-clicked submit must not grade twice: the second request waits here
        # until the first commits, then finds its assessment below.
        await self._interviews.lock(interview_id)
        interview = await self._interviews.get(interview_id)

        existing = await self._assessments.get_for_interview(interview_id)
        if existing is not None:
            # Finalising twice is a double-submit, not an error worth surfacing.
            # The original stored a duplicate record each time.
            logger.info("Interview already assessed; returning stored assessment")
            return existing

        answered = [
            (question, interview.answers[question.id])
            for question in interview.questions
            if question.id in interview.answers
        ]
        if not answered:
            raise InterviewNotReadyError("Cannot assess an interview with no answers")

        question_assessments = await asyncio.gather(
            *(
                self._grader.grade(
                    question=question,
                    answer=answer,
                    seniority=interview.seniority,
                )
                for question, answer in answered
            )
        )

        summary, recommendation = await self._summariser.summarise(
            interview=interview,
            question_assessments=list(question_assessments),
        )

        assessment = Assessment(
            interview_id=interview.id,
            question_assessments=list(question_assessments),
            questions_total=len(interview.questions),
            summary=summary,
            recommendation=Recommendation(recommendation),
        )

        await self._assessments.save(assessment)
        await self._interviews.save(interview.finalised())

        logger.info(
            "Interview assessed: %.1f%% over %d of %d questions, recommendation=%s",
            assessment.score_percentage,
            assessment.questions_answered,
            assessment.questions_total,
            assessment.recommendation,
        )
        return assessment

    async def get_for_interview(self, interview_id: UUID) -> Assessment | None:
        return await self._assessments.get_for_interview(interview_id)
