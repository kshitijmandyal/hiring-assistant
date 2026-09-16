from enum import StrEnum

from talentscout.constants import SENIORITY_THRESHOLDS


class SeniorityLevel(StrEnum):
    """Drives question difficulty. Derived from experience, never set directly."""

    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    PRINCIPAL = "principal"

    @classmethod
    def from_years(cls, years: float) -> "SeniorityLevel":
        for threshold, level in SENIORITY_THRESHOLDS:
            if years >= threshold:
                return cls(level)
        return cls.JUNIOR


class QuestionKind(StrEnum):
    CONCEPTUAL = "conceptual"
    PRACTICAL = "practical"
    DEBUGGING = "debugging"
    DESIGN = "design"


class InterviewStatus(StrEnum):
    DRAFT = "draft"
    QUESTIONS_READY = "questions_ready"
    IN_PROGRESS = "in_progress"
    FINALISED = "finalised"
