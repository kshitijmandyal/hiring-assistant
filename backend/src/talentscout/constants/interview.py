"""Limits and thresholds governing a screening interview."""

from typing import Final

QUESTIONS_PER_TECHNOLOGY: Final = 4
QUESTIONS_PER_TECHNOLOGY_MIN: Final = 3
QUESTIONS_PER_TECHNOLOGY_MAX: Final = 6

TECH_STACK_MAX_SIZE: Final = 10
TECHNOLOGY_NAME_MAX_LENGTH: Final = 40

ANSWER_MIN_LENGTH: Final = 1
ANSWER_MAX_LENGTH: Final = 5_000

YEARS_OF_EXPERIENCE_MAX: Final = 60

# Lower bound in years -> seniority. Scanned highest-first, so order matters.
SENIORITY_THRESHOLDS: Final[tuple[tuple[float, str], ...]] = (
    (8.0, "principal"),
    (5.0, "senior"),
    (2.0, "intermediate"),
    (0.0, "junior"),
)
