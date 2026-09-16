"""Maps exceptions to HTTP responses.

Routers therefore contain no error translation: they let the exception propagate and
it is rendered consistently here, with the same body shape every time.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from talentscout.api.schemas.errors import ErrorResponse
from talentscout.constants import ErrorCode
from talentscout.constants.auth import BEARER_SCHEME
from talentscout.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InterviewStateError,
    LLMError,
    LLMRateLimitedError,
    NotFoundError,
    StorageError,
    TalentScoutError,
    ValidationError,
)
from talentscout.logging_config import get_correlation_id

logger = logging.getLogger(__name__)

_STATUS_BY_CODE: dict[ErrorCode, int] = {
    ErrorCode.LLM_RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.LLM_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.QUESTION_GENERATION_FAILED: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.GRADING_FAILED: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.DUPLICATE_CANDIDATE: status.HTTP_409_CONFLICT,
    ErrorCode.EMAIL_ALREADY_REGISTERED: status.HTTP_409_CONFLICT,
}


def _status_for(exc: TalentScoutError) -> int:
    if (explicit := _STATUS_BY_CODE.get(exc.code)) is not None:
        return explicit
    # Authentication before validation: WeakPasswordError subclasses ValidationError,
    # but a missing or bad credential is 401, not 422.
    if isinstance(exc, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, AuthorizationError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(exc, NotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, ValidationError):
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    if isinstance(exc, InterviewStateError):
        return status.HTTP_409_CONFLICT
    if isinstance(exc, LLMError):
        return status.HTTP_502_BAD_GATEWAY
    if isinstance(exc, StorageError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _body(code: str, message: str, details: dict[str, object] | None = None) -> dict[str, object]:
    return ErrorResponse(
        code=code,
        message=message,
        details=details or {},
        correlation_id=get_correlation_id(),
    ).model_dump()


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(TalentScoutError)
    async def handle_known(_: Request, exc: TalentScoutError) -> JSONResponse:
        http_status = _status_for(exc)
        # 5xx means we broke; 4xx means the caller did. Only the former is a warning.
        log = logger.warning if http_status >= 500 else logger.info
        log("Request failed with %s (%d)", exc.code.value, http_status)

        headers = {}
        if isinstance(exc, LLMRateLimitedError) and exc.retry_after_seconds:
            headers["Retry-After"] = str(exc.retry_after_seconds)
        if http_status == status.HTTP_401_UNAUTHORIZED:
            # Required by RFC 9110 on a 401, and tells clients which scheme to use.
            headers["WWW-Authenticate"] = BEARER_SCHEME

        return JSONResponse(
            status_code=http_status,
            content=_body(exc.code.value, exc.message, exc.details),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_body(
                ErrorCode.VALIDATION_FAILED.value,
                "Request body failed validation",
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(PydanticValidationError)
    async def handle_domain_validation(_: Request, exc: PydanticValidationError) -> JSONResponse:
        """Domain models validate on construction, so a bad value surfaces as a
        Pydantic error from inside a service rather than at the request boundary.
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_body(
                ErrorCode.VALIDATION_FAILED.value,
                "One or more values were rejected",
                {"errors": [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()]},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # No exception text: it can contain candidate data or connection strings.
            content=_body(ErrorCode.INTERNAL_ERROR.value, "An unexpected error occurred"),
        )
