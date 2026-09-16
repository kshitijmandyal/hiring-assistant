"""JWT issuing and verification.

Every token states its own type. Without that claim a refresh token would be accepted
wherever an access token is expected, which turns a long-lived credential into a
permanent session.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from talentscout.constants.auth import (
    ACCESS_TOKEN_TTL_MINUTES,
    INVITE_TOKEN_TTL_DAYS,
    JWT_ALGORITHM,
    JWT_ISSUER,
    REFRESH_TOKEN_TTL_DAYS,
    Role,
    TokenType,
)
from talentscout.domain.user import Principal
from talentscout.exceptions import TokenExpiredError, TokenInvalidError


class TokenService:
    def __init__(self, secret: str) -> None:
        self._secret = secret

    def _encode(
        self,
        *,
        subject_id: UUID,
        role: Role,
        token_type: TokenType,
        ttl: timedelta,
        extra: dict[str, Any] | None = None,
    ) -> tuple[str, str, datetime]:
        now = datetime.now(UTC)
        expires_at = now + ttl
        jti = uuid.uuid4().hex
        payload: dict[str, Any] = {
            "sub": str(subject_id),
            "role": role.value,
            "typ": token_type.value,
            "iss": JWT_ISSUER,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": jti,
            **(extra or {}),
        }
        return jwt.encode(payload, self._secret, algorithm=JWT_ALGORITHM), jti, expires_at

    def issue_access_token(self, *, user_id: UUID) -> str:
        token, _, _ = self._encode(
            subject_id=user_id,
            role=Role.INTERVIEWER,
            token_type=TokenType.ACCESS,
            ttl=timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES),
        )
        return token

    def issue_refresh_token(self, *, user_id: UUID) -> tuple[str, str, datetime]:
        """Returns (token, jti, expires_at). The jti is stored so it can be revoked."""
        return self._encode(
            subject_id=user_id,
            role=Role.INTERVIEWER,
            token_type=TokenType.REFRESH,
            ttl=timedelta(days=REFRESH_TOKEN_TTL_DAYS),
        )

    def issue_invite_token(self, *, candidate_id: UUID, interview_id: UUID) -> str:
        """A candidate's only credential, scoped to exactly one interview."""
        token, _, _ = self._encode(
            subject_id=candidate_id,
            role=Role.CANDIDATE,
            token_type=TokenType.INVITE,
            ttl=timedelta(days=INVITE_TOKEN_TTL_DAYS),
            extra={"interview_id": str(interview_id)},
        )
        return token

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """Named method on the TokenIssuer protocol, so services need not know
        that token types exist at all."""
        return self.decode(token, expected_type=TokenType.REFRESH)

    def decode(self, token: str, *, expected_type: TokenType) -> dict[str, Any]:
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self._secret,
                algorithms=[JWT_ALGORITHM],
                issuer=JWT_ISSUER,
                options={"require": ["exp", "iat", "sub", "jti", "iss"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("This token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError("This token is not valid") from exc

        if payload.get("typ") != expected_type.value:
            # A refresh or invite token presented as an access token.
            raise TokenInvalidError("Wrong token type for this operation")
        return payload

    def principal_from_token(self, token: str) -> Principal:
        """Resolves a bearer token to the caller's identity and scope."""
        unverified_type = self._peek_type(token)
        if unverified_type not in (TokenType.ACCESS, TokenType.INVITE):
            raise TokenInvalidError("This token cannot be used to authenticate a request")

        payload = self.decode(token, expected_type=unverified_type)
        role = Role(payload["role"])
        interview_id = payload.get("interview_id")

        if role is Role.CANDIDATE and not interview_id:
            # A candidate token without a scope would grant access to every interview.
            raise TokenInvalidError("Candidate token is missing its interview scope")

        return Principal(
            subject_id=UUID(payload["sub"]),
            role=role,
            interview_id=UUID(interview_id) if interview_id else None,
        )

    @staticmethod
    def _peek_type(token: str) -> TokenType | None:
        """Reads `typ` without verifying, only to choose which check to run.

        The signature is still verified by decode() immediately afterwards, so nothing
        here is trusted.
        """
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            return TokenType(unverified.get("typ", ""))
        except (jwt.InvalidTokenError, ValueError):
            raise TokenInvalidError("This token is not valid") from None
