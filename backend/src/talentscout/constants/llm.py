"""Claude model configuration and prompt identifiers."""

from enum import StrEnum
from typing import Final

CLAUDE_MODEL: Final = "claude-opus-5"
CLAUDE_MAX_TOKENS: Final = 16_000


class PromptId(StrEnum):
    """Identifies a template under adapters/claude/prompts/.

    Versioned in the filename so a prompt change is a new file rather than an edit,
    keeping generated questions traceable to the prompt that produced them.
    """

    QUESTION_GENERATOR = "question_generator"
    GRADER = "grader"
    SUMMARISER = "summariser"


QUESTION_GENERATOR_PROMPT: Final = PromptId.QUESTION_GENERATOR
GRADER_PROMPT: Final = PromptId.GRADER
SUMMARISER_PROMPT: Final = PromptId.SUMMARISER
