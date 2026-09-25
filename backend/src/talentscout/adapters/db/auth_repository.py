"""Persistence for users and refresh-token sessions."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from talentscout.adapters.db.orm import RefreshTokenRow, UserRow
from talentscout.domain.user import User
from talentscout.exceptions import EmailAlreadyRegisteredError, StorageError
from talentscout.mappers import user_mapper


class PostgresUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        self._session.add(user_mapper.to_row(user))
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError("That email is already registered") from exc
        except SQLAlchemyError as exc:
            raise StorageError("Could not store user") from exc

    async def find_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserRow).where(UserRow.email == email.lower()))
        row = result.scalar_one_or_none()
        return user_mapper.to_domain(row) if row else None

    async def get(self, user_id: UUID) -> User | None:
        row = await self._session.get(UserRow, user_id)
        return user_mapper.to_domain(row) if row else None


class PostgresRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store(self, *, user_id: UUID, jti: str, expires_at: datetime) -> None:
        self._session.add(
            RefreshTokenRow(
                id=uuid4(),
                user_id=user_id,
                jti=jti,
                expires_at=expires_at,
                created_at=datetime.now(UTC),
            )
        )
        await self._session.flush()

    async def is_active(self, jti: str) -> bool:
        """A token is usable only if we issued it and have not revoked it."""
        result = await self._session.execute(
            select(RefreshTokenRow).where(RefreshTokenRow.jti == jti)
        )
        row = result.scalar_one_or_none()
        if row is None or row.revoked_at is not None:
            return False
        return row.expires_at > datetime.now(UTC)

    async def revoke(self, jti: str) -> None:
        result = await self._session.execute(
            select(RefreshTokenRow).where(RefreshTokenRow.jti == jti)
        )
        row = result.scalar_one_or_none()
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
            await self._session.flush()
