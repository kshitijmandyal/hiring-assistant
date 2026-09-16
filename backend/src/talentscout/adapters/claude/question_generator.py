import logging

from talentscout.adapters.claude.client import ClaudeClient
from talentscout.adapters.claude.schemas import LLMQuestionSet
from talentscout.constants import QUESTION_GENERATOR_PROMPT
from talentscout.domain.enums import SeniorityLevel
from talentscout.domain.interview import Question
from talentscout.exceptions import LLMError, QuestionGenerationError
from talentscout.mappers.question_mapper import to_domain_questions

logger = logging.getLogger(__name__)


class ClaudeQuestionGenerator:
    """Generates screening questions for one technology at a time."""

    def __init__(self, client: ClaudeClient) -> None:
        self._client = client

    async def generate(
        self,
        *,
        technology: str,
        seniority: SeniorityLevel,
        count: int,
    ) -> list[Question]:
        user_content = (
            f"Technology: {technology}\n"
            f"Candidate seniority: {seniority.value}\n"
            f"Write exactly {count} questions."
        )

        try:
            question_set = await self._client.parse(
                prompt_id=QUESTION_GENERATOR_PROMPT,
                user_content=user_content,
                output_format=LLMQuestionSet,
            )
        except LLMError:
            raise
        except Exception as exc:
            raise QuestionGenerationError(f"Could not generate questions for {technology}") from exc

        questions = to_domain_questions(question_set, technology=technology)
        if not questions:
            raise QuestionGenerationError(f"Claude returned no questions for {technology}")

        # The model may return fewer than asked; that is better than the previous
        # behaviour of padding with "Additional question 1 about React."
        if len(questions) != count:
            logger.warning(
                "Asked for %d questions on %s, got %d", count, technology, len(questions)
            )

        return questions[:count]
