#!/usr/bin/env python
"""Apply database migrations.

On a long-lived host this runs on boot. Serverless has no boot, so it runs as the
build step instead (see `[tool.vercel.scripts]` in pyproject.toml), and manually
against a new database:

    cd backend && DATABASE_URL="<direct neon url>" uv run python scripts/migrate.py

Use the **direct** Neon host, not the pooled one — Postgres will not reliably pass
DDL through a transaction pooler.
"""

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        # A build before the database exists is not a migration failure. Failing here
        # would block the very first deploy, which is when there is nothing to migrate.
        print("DATABASE_URL is not set — skipping migrations.", file=sys.stderr)
        print(
            "Set it on the project and redeploy, or run this script by hand against "
            "the direct database host.",
            file=sys.stderr,
        )
        return

    backend_root = Path(__file__).resolve().parent.parent
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    print("Migrations applied.", file=sys.stderr)


if __name__ == "__main__":
    main()
