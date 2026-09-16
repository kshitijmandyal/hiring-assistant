import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from talentscout.adapters.db.orm import Base
from talentscout.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _database_url() -> str:
    """DATABASE_URL first, Settings second.

    Migrations run in build environments that have the database URL but not the
    application's other secrets, so requiring a full Settings object here would make
    a deploy fail for want of an API key it never uses.
    """
    if url := os.environ.get("DATABASE_URL"):
        return url
    return str(get_settings().database_url)


# No credentials in alembic.ini; the URL is resolved at runtime.
config.set_main_option("sqlalchemy.url", _database_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
