"""Assessment mapping: LLM schema -> domain, and domain <-> ORM rows."""

from uuid import UUID, uuid4

from talentscout.adapters.claude.schemas import LLMCriterionScore, LLMGrade, LLMSummary
from talentscout.adapters.db.orm import (
    AssessmentRow,
    CriterionScoreRow,
    QuestionAssessmentRow,
)
from talentscout.domain.assessment import (
    Assessment,
    CriterionScore,
    QuestionAssessment,
    Recommendation,
)


def to_domain_criterion_score(llm_score: LLMCriterionScore) -> CriterionScore:
    return CriterionScore(
        criterion=llm_score.criterion,
        met=llm_score.met,
        justification=llm_score.justification,
    )


def to_domain_question_assessment(
    grade: LLMGrade,
    *,
    question_id: UUID,
    guardrail_flags: list[str] | None = None,
) -> QuestionAssessment:
    return QuestionAssessment(
        question_id=question_id,
        score=grade.score,
        criterion_scores=[to_domain_criterion_score(cs) for cs in grade.criterion_scores],
        strengths=grade.strengths,
        gaps=grade.gaps,
        guardrail_flags=guardrail_flags or [],
    )


def to_recommendation(summary: LLMSummary) -> Recommendation:
    """Falls back to BORDERLINE rather than raising: an unrecognised label is a prompt
    drift problem, and losing an otherwise complete assessment over it helps nobody.
    """
    try:
        return Recommendation(summary.recommendation.strip().lower())
    except ValueError:
        return Recommendation.BORDERLINE


# --- ORM ---------------------------------------------------------------------


def to_row(assessment: Assessment) -> AssessmentRow:
    return AssessmentRow(
        id=uuid4(),
        interview_id=assessment.interview_id,
        questions_total=assessment.questions_total,
        summary=assessment.summary,
        recommendation=assessment.recommendation.value,
        assessed_at=assessment.assessed_at,
        question_assessments=[
            _question_assessment_to_row(qa) for qa in assessment.question_assessments
        ],
    )


def _question_assessment_to_row(qa: QuestionAssessment) -> QuestionAssessmentRow:
    return QuestionAssessmentRow(
        id=uuid4(),
        question_id=qa.question_id,
        score=qa.score,
        strengths=list(qa.strengths),
        gaps=list(qa.gaps),
        guardrail_flags=list(qa.guardrail_flags),
        criterion_scores=[
            CriterionScoreRow(
                id=uuid4(),
                criterion=cs.criterion,
                met=cs.met,
                justification=cs.justification,
            )
            for cs in qa.criterion_scores
        ],
    )


def to_domain_assessment(row: AssessmentRow) -> Assessment:
    return Assessment(
        interview_id=row.interview_id,
        questions_total=row.questions_total,
        summary=row.summary,
        recommendation=Recommendation(row.recommendation),
        assessed_at=row.assessed_at,
        question_assessments=[
            QuestionAssessment(
                question_id=qa.question_id,
                score=qa.score,
                criterion_scores=[
                    CriterionScore(
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
            for qa in row.question_assessments
        ],
    )
