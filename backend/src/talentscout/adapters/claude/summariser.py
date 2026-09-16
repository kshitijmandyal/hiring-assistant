import logging

from talentscout.adapters.claude.client import ClaudeClient
from talentscout.adapters.claude.schemas import LLMSummary
from talentscout.constants import SUMMARISER_PROMPT
from talentscout.domain.assessment import QuestionAssessment
from talentscout.domain.interview import Interview
from talentscout.exceptions import GradingError, LLMError
from talentscout.mappers.assessment_mapper import to_recommendation

logger = logging.getLogger(__name__)


class ClaudeAssessmentSummariser:
    """Turns per-question grades into a hiring-manager summary and a recommendation."""

    def __init__(self, client: ClaudeClient) -> None:
        self._client = client

    async def summarise(
        self,
        *,
        interview: Interview,
        question_assessments: list[QuestionAssessment],
    ) -> tuple[str, str]:
        questions_by_id = {q.id: q for q in interview.questions}
        lines = []
        for assessment in question_assessments:
            question = questions_by_id.get(assessment.question_id)
            technology = question.technology if question else "unknown"
            met = sum(1 for cs in assessment.criterion_scores if cs.met)
            lines.append(
                f"- {technology} ({assessment.score}/10, "
                f"{met}/{len(assessment.criterion_scores)} rubric criteria met)"
                + (f" gaps: {'; '.join(assessment.gaps)}" if assessment.gaps else "")
            )

        user_content = (
            f"Candidate seniority: {interview.seniority.value}\n"
            f"Declared tech stack: {', '.join(interview.tech_stack)}\n"
            f"Answered {len(question_assessments)} of {len(interview.questions)} questions.\n\n"
            "Per-question results:\n" + "\n".join(lines)
        )

        try:
            summary = await self._client.parse(
                prompt_id=SUMMARISER_PROMPT,
                user_content=user_content,
                output_format=LLMSummary,
            )
        except LLMError:
            raise
        except Exception as exc:
            raise GradingError("Could not summarise this interview") from exc

        return summary.summary, to_recommendation(summary).value
