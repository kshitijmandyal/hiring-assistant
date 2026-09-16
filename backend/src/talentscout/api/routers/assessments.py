from uuid import UUID

from fastapi import APIRouter, status

from talentscout.api.dependencies import AssessmentServiceDep, InterviewerDep
from talentscout.api.schemas.assessment import AssessmentResponse
from talentscout.exceptions import InterviewNotFoundError
from talentscout.mappers import api_mapper

# Interviewer-only throughout: grading spends Claude credits, and the response
# carries rubric criteria, which are the answer key.
router = APIRouter(prefix="/interviews", tags=["assessments"])


@router.post("/{interview_id}/assessment", status_code=status.HTTP_201_CREATED)
async def finalise_interview(
    interview_id: UUID,
    assessments: AssessmentServiceDep,
    _: InterviewerDep,
) -> AssessmentResponse:
    """Grades every answered question and closes the interview.

    Idempotent: finalising twice returns the stored assessment rather than regrading.
    """
    assessment = await assessments.finalise(interview_id)
    return api_mapper.to_assessment_response(assessment)


@router.get("/{interview_id}/assessment")
async def get_assessment(
    interview_id: UUID,
    assessments: AssessmentServiceDep,
    _: InterviewerDep,
) -> AssessmentResponse:
    assessment = await assessments.get_for_interview(interview_id)
    if assessment is None:
        raise InterviewNotFoundError("This interview has not been assessed yet")
    return api_mapper.to_assessment_response(assessment)
