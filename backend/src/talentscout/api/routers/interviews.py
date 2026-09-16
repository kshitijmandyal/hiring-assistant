from uuid import UUID

from fastapi import APIRouter, status

from talentscout.api.dependencies import (
    AuthServiceDep,
    InterviewAccessDep,
    InterviewerDep,
    ScreeningServiceDep,
)
from talentscout.api.schemas.auth import InviteResponse
from talentscout.api.schemas.interview import (
    AnswerSubmitRequest,
    InterviewResponse,
    InterviewStartRequest,
)
from talentscout.constants.auth import INVITE_TOKEN_TTL_DAYS
from talentscout.domain.interview import Answer
from talentscout.mappers import api_mapper

router = APIRouter(tags=["interviews"])


@router.post("/candidates/{candidate_id}/interviews", status_code=status.HTTP_201_CREATED)
async def start_interview(
    candidate_id: UUID,
    request: InterviewStartRequest,
    screening: ScreeningServiceDep,
    _: InterviewerDep,
) -> InterviewResponse:
    """Generates the question set. Interviewer-only — this is the expensive call."""
    interview = await screening.start_interview(
        candidate_id=candidate_id,
        tech_stack=request.tech_stack,
        questions_per_technology=request.questions_per_technology,
    )
    return api_mapper.to_interview_response(interview)


@router.post("/interviews/{interview_id}/invite")
async def create_invite(
    interview_id: UUID,
    screening: ScreeningServiceDep,
    auth: AuthServiceDep,
    _: InterviewerDep,
) -> InviteResponse:
    """Mints the candidate's link.

    The token is scoped to this one interview, so it grants nothing else even if the
    link is forwarded.
    """
    interview = await screening.get_interview(interview_id)
    token = auth.issue_invite(candidate_id=interview.candidate_id, interview_id=interview.id)
    return InviteResponse(
        interview_id=interview.id,
        invite_token=token,
        expires_in_days=INVITE_TOKEN_TTL_DAYS,
    )


@router.get("/interviews/{interview_id}")
async def get_interview(
    interview_id: UUID,
    screening: ScreeningServiceDep,
    _: InterviewAccessDep,
) -> InterviewResponse:
    interview = await screening.get_interview(interview_id)
    return api_mapper.to_interview_response(interview)


@router.post("/interviews/{interview_id}/answers")
async def submit_answer(
    interview_id: UUID,
    request: AnswerSubmitRequest,
    screening: ScreeningServiceDep,
    _: InterviewAccessDep,
) -> InterviewResponse:
    interview = await screening.record_answer(
        interview_id=interview_id,
        answer=Answer(question_id=request.question_id, text=request.text),
    )
    return api_mapper.to_interview_response(interview)
