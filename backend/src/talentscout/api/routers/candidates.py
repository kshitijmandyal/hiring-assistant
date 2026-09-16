from uuid import UUID

from fastapi import APIRouter, status

from talentscout.api.dependencies import InterviewerDep, ScreeningServiceDep
from talentscout.api.schemas.candidate import CandidateCreateRequest, CandidateResponse
from talentscout.mappers import api_mapper

# Interviewer-only: candidate records hold personal data, and creating one is the
# first step of a flow that ends in paid Claude calls.
router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_candidate(
    request: CandidateCreateRequest,
    screening: ScreeningServiceDep,
    _: InterviewerDep,
) -> CandidateResponse:
    candidate = await screening.register_candidate(api_mapper.to_candidate(request))
    return api_mapper.to_candidate_response(candidate)


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: UUID,
    screening: ScreeningServiceDep,
    _: InterviewerDep,
) -> CandidateResponse:
    candidate = await screening.get_candidate(candidate_id)
    return api_mapper.to_candidate_response(candidate)
