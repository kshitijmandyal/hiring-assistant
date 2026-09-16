"""Authentication use cases.

Depends only on protocols, so the password hasher and token format are adapter
choices rather than something this layer knows about.
"""

import logging
import secrets
from uuid import UUID

from talentscout.domain.user import User
from talentscout.exceptions import InvalidCredentialsError, TokenInvalidError
from talentscout.interfaces import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenIssuer,
    UserRepository,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        tokens: TokenIssuer,
        passwords: PasswordHasher,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._tokens = tokens
        self._passwords = passwords

    async def register(self, *, email: str, full_name: str, password: str) -> User:
        user = User(
            email=email,
            full_name=full_name,
            password_hash=self._passwords.hash(password),
        )
        await self._users.add(user)
        logger.info("Interviewer registered")
        return user

    async def login(self, *, email: str, password: str) -> tuple[str, str]:
        """Returns (access_token, refresh_token)."""
        user = await self._users.find_by_email(email)

        if user is None:
            # Verify against a real hash anyway, so an unknown email costs the same
            # time as a wrong password; otherwise this endpoint enumerates users.
            self._passwords.verify(password, self._decoy_hash())
            raise InvalidCredentialsError("Email or password is incorrect")

        if not self._passwords.verify(password, user.password_hash):
            raise InvalidCredentialsError("Email or password is incorrect")

        if not user.is_active:
            raise InvalidCredentialsError("This account is disabled")

        logger.info("Login succeeded")
        return await self._issue_pair(user.id)

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        payload = self._tokens.decode_refresh_token(refresh_token)
        jti = str(payload["jti"])

        if not await self._refresh_tokens.is_active(jti):
            raise TokenInvalidError("This session is no longer valid")

        # Rotation: the presented token is burned as the new pair is issued, so a
        # stolen refresh token is usable at most once.
        await self._refresh_tokens.revoke(jti)
        return await self._issue_pair(UUID(str(payload["sub"])))

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = self._tokens.decode_refresh_token(refresh_token)
        except TokenInvalidError:
            return  # Logging out with an already-dead token is not an error.
        await self._refresh_tokens.revoke(str(payload["jti"]))

    async def revoke_all_sessions(self, user_id: UUID) -> None:
        await self._refresh_tokens.revoke_all_for_user(user_id)

    def issue_invite(self, *, candidate_id: UUID, interview_id: UUID) -> str:
        return self._tokens.issue_invite_token(candidate_id=candidate_id, interview_id=interview_id)

    def _decoy_hash(self) -> str:
        """A genuine hash of a random secret, produced once per process.

        It must be real: a malformed hash would be rejected during parsing and return
        far faster than a true verification, which is the timing signal this exists
        to remove. The value never matches a user-supplied password.
        """
        global _DECOY_HASH
        if _DECOY_HASH is None:
            _DECOY_HASH = self._passwords.hash(secrets.token_urlsafe(32))
        return _DECOY_HASH

    async def _issue_pair(self, user_id: UUID) -> tuple[str, str]:
        access = self._tokens.issue_access_token(user_id=user_id)
        refresh, jti, expires_at = self._tokens.issue_refresh_token(user_id=user_id)
        await self._refresh_tokens.store(user_id=user_id, jti=jti, expires_at=expires_at)
        return access, refresh


# Computed on first use and reused for the life of the process.
_DECOY_HASH: str | None = None
