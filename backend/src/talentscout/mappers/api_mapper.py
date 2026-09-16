"""Domain models -> API response schemas."""

from talentscout.api.schemas.assessment import (
    AssessmentResponse,
    CriterionScoreResponse,
    QuestionAssessmentResponse,
)
from talentscout.api.schemas.candidate import CandidateCreateRequest, CandidateResponse
from talentscout.api.schemas.interview import InterviewResponse, QuestionResponse
from talentscout.domain.assessment import Assessment, QuestionAssessment
from talentscout.domain.candidate import Candidate
from talentscout.domain.interview import Interview, Question


def to_candidate(request: CandidateCreateRequest) -> Candidate:
    """Request -> domain. Domain validators do the real checking; a malformed email
    raises here rather than reaching the database.
    """
    return Candidate(
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
        years_of_experience=request.years_of_experience,
        desired_positions=request.desired_positions,
        location=request.location,
    )


def to_candidate_response(candidate: Candidate) -> CandidateResponse:
    return CandidateResponse(
        id=candidate.id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        years_of_experience=candidate.years_of_experience,
        desired_positions=list(candidate.desired_positions),
        location=candidate.location,
        seniority=candidate.seniority.value,
        created_at=candidate.created_at,
    )


def to_question_response(question: Question) -> QuestionResponse:
    return QuestionResponse(
        id=question.id,
        technology=question.technology,
        prompt=question.prompt,
        kind=question.kind.value,
    )


def to_interview_response(interview: Interview) -> InterviewResponse:
    return InterviewResponse(
        id=interview.id,
        candidate_id=interview.candidate_id,
        seniority=interview.seniority.value,
        tech_stack=list(interview.tech_stack),
        status=interview.status.value,
        questions=[to_question_response(q) for q in interview.questions],
        answered_question_ids=list(interview.answers.keys()),
        created_at=interview.created_at,
        finalised_at=interview.finalised_at,
    )


def to_question_assessment_response(qa: QuestionAssessment) -> QuestionAssessmentResponse:
    return QuestionAssessmentResponse(
        question_id=qa.question_id,
        score=qa.score,
        criterion_scores=[
            CriterionScoreResponse(
                criterion=cs.criterion,
                met=cs.met,
                justification=cs.justification,
            )
            for cs in qa.criterion_scores
        ],
        strengths=list(qa.strengths),
        gaps=list(qa.gaps),
        guardrail_flags=list(qa.guardrail_flags),
    )


def to_assessment_response(assessment: Assessment) -> AssessmentResponse:
    return AssessmentResponse(
        interview_id=assessment.interview_id,
        question_assessments=[
            to_question_assessment_response(qa) for qa in assessment.question_assessments
        ],
        questions_answered=assessment.questions_answered,
        questions_total=assessment.questions_total,
        coverage=round(assessment.coverage, 4),
        average_score=round(assessment.average_score, 2),
        score_percentage=round(assessment.score_percentage, 1),
        summary=assessment.summary,
        recommendation=assessment.recommendation.value,
        assessed_at=assessment.assessed_at,
    )
