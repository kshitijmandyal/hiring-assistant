"""Application exception hierarchy.

Every error carries an ErrorCode so the API layer can map it to an HTTP response
without inspecting types, and clients can branch on a stable string.
"""

from typing import Any

from talentscout.constants import ErrorCode


class TalentScoutError(Exception):
    """Base for every error this application raises deliberately."""

    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# --- Input validation -------------------------------------------------------


class ValidationError(TalentScoutError):
    code = ErrorCode.VALIDATION_FAILED


class InvalidEmailError(ValidationError):
    code = ErrorCode.INVALID_EMAIL


class InvalidPhoneError(ValidationError):
    code = ErrorCode.INVALID_PHONE


class InvalidExperienceError(ValidationError):
    code = ErrorCode.INVALID_EXPERIENCE


class EmptyTechStackError(ValidationError):
    code = ErrorCode.EMPTY_TECH_STACK


class TechStackTooLargeError(ValidationError):
    code = ErrorCode.TECH_STACK_TOO_LARGE


# --- Lookup -----------------------------------------------------------------


class NotFoundError(TalentScoutError):
    """Base for anything the caller asked for that does not exist."""


class CandidateNotFoundError(NotFoundError):
    code = ErrorCode.CANDIDATE_NOT_FOUND


class InterviewNotFoundError(NotFoundError):
    code = ErrorCode.INTERVIEW_NOT_FOUND


class QuestionNotFoundError(NotFoundError):
    code = ErrorCode.QUESTION_NOT_FOUND


class DuplicateCandidateError(TalentScoutError):
    code = ErrorCode.DUPLICATE_CANDIDATE


# --- Interview lifecycle ----------------------------------------------------


class InterviewStateError(TalentScoutError):
    """The interview is not in a state that permits the requested transition."""


class InterviewAlreadyFinalisedError(InterviewStateError):
    code = ErrorCode.INTERVIEW_ALREADY_FINALISED


class InterviewNotReadyError(InterviewStateError):
    code = ErrorCode.INTERVIEW_NOT_READY


# --- LLM --------------------------------------------------------------------


class LLMError(TalentScoutError):
    """Base for failures originating in the language model adapter."""


class LLMUnavailableError(LLMError):
    code = ErrorCode.LLM_UNAVAILABLE


class LLMRateLimitedError(LLMError):
    code = ErrorCode.LLM_RATE_LIMITED

    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.retry_after_seconds = retry_after_seconds


class QuestionGenerationError(LLMError):
    code = ErrorCode.QUESTION_GENERATION_FAILED


class GradingError(LLMError):
    code = ErrorCode.GRADING_FAILED


# --- Authentication and authorisation ---


class AuthenticationError(TalentScoutError):
    """The caller is not who they claim to be, or did not say."""

    code = ErrorCode.NOT_AUTHENTICATED


class InvalidCredentialsError(AuthenticationError):
    code = ErrorCode.INVALID_CREDENTIALS


class TokenExpiredError(AuthenticationError):
    code = ErrorCode.TOKEN_EXPIRED


class TokenInvalidError(AuthenticationError):
    code = ErrorCode.TOKEN_INVALID


class AuthorizationError(TalentScoutError):
    """Authenticated, but not permitted to do this."""

    code = ErrorCode.FORBIDDEN


class WeakPasswordError(ValidationError):
    code = ErrorCode.WEAK_PASSWORD


class EmailAlreadyRegisteredError(TalentScoutError):
    code = ErrorCode.EMAIL_ALREADY_REGISTERED


# --- Persistence ------------------------------------------------------------


class StorageError(TalentScoutError):
    code = ErrorCode.STORAGE_FAILED
