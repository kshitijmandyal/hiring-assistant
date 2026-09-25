"""Brute-force limits backed by Postgres, so every serverless instance shares one count."""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from talentscout.adapters.db.orm import AuthAttemptRow
from talentscout.constants.auth import (
    LOGIN_FAILURES_PER_EMAIL,
    LOGIN_FAILURES_PER_IP,
    LOGIN_WINDOW_MINUTES,
    REGISTER_WINDOW_MINUTES,
    REGISTRATIONS_PER_IP,
    AttemptKind,
)

_LIMITS: dict[AttemptKind, tuple[int, timedelta]] = {
    AttemptKind.LOGIN_EMAIL: (LOGIN_FAILURES_PER_EMAIL, timedelta(minutes=LOGIN_WINDOW_MINUTES)),
    AttemptKind.LOGIN_IP: (LOGIN_FAILURES_PER_IP, timedelta(minutes=LOGIN_WINDOW_MINUTES)),
    AttemptKind.REGISTER_IP: (REGISTRATIONS_PER_IP, timedelta(minutes=REGISTER_WINDOW_MINUTES)),
}


def _digest(key: str) -> str:
    return hashlib.sha256(key.strip().lower().encode()).hexdigest()


class PostgresAttemptLimiter:
    """Uses its own short sessions rather than the request's, so a recorded failure
    commits even though the login that caused it raises and rolls back.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def retry_after(self, kind: AttemptKind, key: str) -> int | None:
        limit, window = _LIMITS[kind]
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            count, oldest = (
                await session.execute(
                    select(func.count(), func.min(AuthAttemptRow.created_at)).where(
                        AuthAttemptRow.kind == kind.value,
                        AuthAttemptRow.key == _digest(key),
                        AuthAttemptRow.created_at > now - window,
                    )
                )
            ).one()
        if count < limit or oldest is None:
            return None
        # The oldest attempt ageing out is what frees the next slot.
        return max(1, int((oldest + window - now).total_seconds()))

    async def record(self, kind: AttemptKind, key: str) -> None:
        _, window = _LIMITS[kind]
        now = datetime.now(UTC)
        async with self._session_factory() as session, session.begin():
            session.add(
                AuthAttemptRow(id=uuid4(), kind=kind.value, key=_digest(key), created_at=now)
            )
            await session.execute(
                delete(AuthAttemptRow).where(
                    AuthAttemptRow.kind == kind.value,
                    AuthAttemptRow.created_at <= now - window,
                )
            )

    async def clear(self, kind: AttemptKind, key: str) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(
                delete(AuthAttemptRow).where(
                    AuthAttemptRow.kind == kind.value,
                    AuthAttemptRow.key == _digest(key),
                )
            )
