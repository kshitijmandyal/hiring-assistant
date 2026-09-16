#!/usr/bin/env python
"""Apply database migrations.

On a long-lived host this runs on boot. Serverless has no boot, so run it manually
after deploying a change that touches the schema:

    cd backend && uv run python scripts/migrate.py

Point DATABASE_URL at the **direct** (non-pooled) Neon host when running this —
Postgres refuses some DDL through a transaction pooler.
"""

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


def main() -> int:
    backend_root = Path(__file__).resolve().parent.parent
    config = Config(str(backend_root / "alembic.ini"))
    command.upgrade(config, "head")
    return 0


if __name__ == "__main__":
    sys.exit(main())
