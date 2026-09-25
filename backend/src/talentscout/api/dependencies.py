"""Dependency wiring and access control.

The only module that knows which concrete adapter satisfies which protocol. Routers
depend on services; services depend on protocols; nothing above the adapters layer
names Claude, Postgres, or JWT.
"""

from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from talentscout.adapters.claude.client import ClaudeClient
from talentscout.adapters.claude.grader import ClaudeAnswerGrader
from talentscout.adapters.claude.question_generator import ClaudeQuestionGenerator
from talentscout.adapters.claude.summariser import ClaudeAssessmentSummariser
from talentscout.adapters.db.attempt_limiter import PostgresAttemptLimiter
from talentscout.adapters.db.auth_repository import (
    PostgresRefreshTokenRepository,
    PostgresUserRepository,
)
from talentscout.adapters.db.repositories import (
    PostgresAssessmentRepository,
    PostgresCandidateRepository,
    PostgresInterviewRepository,
)
from talentscout.adapters.security.hasher import BcryptPasswordHasher
from talentscout.adapters.security.tokens import TokenService
from talentscout.config import Settings, get_settings
from talentscout.domain.user import Principal, User
from talentscout.exceptions import AuthenticationError, AuthorizationError
from talentscout.services.assessment import AssessmentService
from talentscout.services.auth import AuthService
from talentscout.services.screening import ScreeningService

# auto_error=False so a missing header raises our own error shape, not FastAPI's.
_bearer = HTTPBearer(auto_error=False)


def get_app_settings() -> Settings:
    return get_settings()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One transaction per request: commit on success, roll back on any exception."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_claude_client(request: Request) -> ClaudeClient:
    client: ClaudeClient = request.app.state.claude_client
    return client


def get_token_service(request: Request) -> TokenService:
    service: TokenService = request.app.state.token_service
    return service


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClaudeDep = Annotated[ClaudeClient, Depends(get_claude_client)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


# --- Services ---------------------------------------------------------------


def get_auth_service(request: Request, session: SessionDep, tokens: TokenServiceDep) -> AuthService:
    return AuthService(
        users=PostgresUserRepository(session),
        refresh_tokens=PostgresRefreshTokenRepository(session),
        tokens=tokens,
        passwords=BcryptPasswordHasher(),
        limiter=PostgresAttemptLimiter(request.app.state.session_factory),
    )


def get_screening_service(session: SessionDep, claude: ClaudeDep) -> ScreeningService:
    return ScreeningService(
        candidates=PostgresCandidateRepository(session),
        interviews=PostgresInterviewRepository(session),
        question_generator=ClaudeQuestionGenerator(claude),
    )


def get_assessment_service(session: SessionDep, claude: ClaudeDep) -> AssessmentService:
    return AssessmentService(
        interviews=PostgresInterviewRepository(session),
        assessments=PostgresAssessmentRepository(session),
        grader=ClaudeAnswerGrader(claude),
        summariser=ClaudeAssessmentSummariser(claude),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_client_ip(request: Request) -> str:
    """Vercel sets x-real-ip itself and drops any client-sent value, so it cannot be
    spoofed there. Locally there is no proxy and the socket address is the client.
    """
    if forwarded := request.headers.get("x-real-ip"):
        return forwarded
    return request.client.host if request.client else "unknown"


ClientIpDep = Annotated[str, Depends(get_client_ip)]
ScreeningServiceDep = Annotated[ScreeningService, Depends(get_screening_service)]
AssessmentServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]


# --- Access control ---------------------------------------------------------


def get_principal(
    tokens: TokenServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if credentials is None:
        raise AuthenticationError("Authentication required")
    return tokens.principal_from_token(credentials.credentials)


PrincipalDep = Annotated[Principal, Depends(get_principal)]


async def get_current_user(principal: PrincipalDep, session: SessionDep) -> User:
    """Guards everything that costs money or exposes grading internals.

    Question generation and grading both call Claude, so leaving them open would let
    anyone spend the account's credits. The user row is re-read on every request so a
    disabled account loses access at once, not when its access token expires.
    """
    if not principal.is_interviewer:
        raise AuthorizationError("This action requires an interviewer account")
    user = await PostgresUserRepository(session).get(principal.subject_id)
    if user is None or not user.is_active:
        # The token is validly signed but the account behind it is gone or disabled.
        raise AuthenticationError("This account is no longer active")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_interviewer(_user: CurrentUserDep, principal: PrincipalDep) -> Principal:
    return principal


InterviewerDep = Annotated[Principal, Depends(require_interviewer)]


def require_interview_access(
    principal: PrincipalDep,
    interview_id: Annotated[UUID, Path()],
) -> Principal:
    """Interviewers reach any interview; a candidate reaches only their own.

    The scope comes from the signed token, never from the request body, so a candidate
    cannot reach another interview by changing the id they send.
    """
    if not principal.may_access_interview(interview_id):
        raise AuthorizationError("You do not have access to this interview")
    return principal


InterviewAccessDep = Annotated[Principal, Depends(require_interview_access)]
