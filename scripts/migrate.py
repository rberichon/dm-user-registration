#!/usr/bin/env python3
"""
Custom database migration runner.

Usage:
    uv run python scripts/migrate.py          # apply all pending migrations
    uv run python scripts/migrate.py up       # same as above
    uv run python scripts/migrate.py down     # rollback the last migration
    uv run python scripts/migrate.py down 3   # rollback the last 3 migrations
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def _build_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    # asyncpg uses postgresql://, not postgresql+asyncpg://
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def _connect() -> asyncpg.Connection:
    return await asyncpg.connect(_build_dsn())


async def _ensure_migrations_table(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    TEXT        PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)


async def _applied_versions(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch(
        "SELECT version FROM schema_migrations ORDER BY version"
    )
    return {row["version"] for row in rows}


def _migration_files(direction: str) -> list[tuple[str, Path]]:
    """Return sorted (version, path) pairs for the given direction."""
    files = sorted(MIGRATIONS_DIR.glob(f"*.{direction}.sql"))
    return [(f.name.split(".")[0], f) for f in files]


async def _execute_script(conn: asyncpg.Connection, sql: str) -> None:
    """Execute a SQL script that may contain multiple statements."""
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            await conn.execute(stmt)


async def migrate_up(conn: asyncpg.Connection) -> None:
    applied = await _applied_versions(conn)
    pending = [(v, p) for v, p in _migration_files("up") if v not in applied]
    if not pending:
        print("Nothing to migrate.")
        return
    for version, path in pending:
        print(f"Applying {path.name} ...")
        async with conn.transaction():
            await _execute_script(conn, path.read_text())
            await conn.execute(
                "INSERT INTO schema_migrations (version) VALUES ($1)",
                version,
            )
        print(f"  OK {version}")


async def migrate_down(conn: asyncpg.Connection, steps: int) -> None:
    applied = sorted(await _applied_versions(conn), reverse=True)
    down_index = dict(_migration_files("down"))
    for version in applied[:steps]:
        if version not in down_index:
            print(f"No down migration for {version}, skipping.")
            continue
        path = down_index[version]
        print(f"Rolling back {path.name} ...")
        async with conn.transaction():
            await _execute_script(conn, path.read_text())
            await conn.execute(
                "DELETE FROM schema_migrations WHERE version = $1",
                version,
            )
        print(f"  OK {version}")


async def main() -> None:
    args = sys.argv[1:]
    command = args[0] if args else "up"
    steps = int(args[1]) if len(args) > 1 else 1

    conn = await _connect()
    try:
        await _ensure_migrations_table(conn)
        if command in ("up", ""):
            await migrate_up(conn)
        elif command == "down":
            await migrate_down(conn, steps)
        else:
            print(f"Unknown command '{command}'. Use 'up' or 'down'.")
            sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
