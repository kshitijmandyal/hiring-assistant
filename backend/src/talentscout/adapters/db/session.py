from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False keeps mapped attributes readable after commit, which
    # matters because repositories map rows to domain objects after flushing.
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """One transaction per unit of work. Commits on success, rolls back on any error."""
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
