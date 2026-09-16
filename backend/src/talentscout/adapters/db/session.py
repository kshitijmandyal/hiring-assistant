from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(
    database_url: str,
    *,
    echo: bool = False,
    serverless: bool = False,
) -> AsyncEngine:
    """Create the engine.

    On serverless the process is torn down between requests, so SQLAlchemy's own pool
    would hold connections that never get reused and are never cleanly closed — enough
    concurrent invocations and the database refuses new ones. NullPool opens and closes
    per session and leaves the pooling to the provider's connection pooler (use Neon's
    `-pooler` host).
    """
    if serverless:
        return create_async_engine(database_url, echo=echo, poolclass=NullPool)
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
