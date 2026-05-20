from datetime import datetime

import asyncpg

from app.domain import ActivationCode


class ActivationCodeRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def upsert(
        self, user_id: int, code: str, expires_at: datetime
    ) -> None:
        """Replace the existing unused code for this user, if any."""
        async with self._conn.transaction():
            await self._conn.execute(
                "DELETE FROM activation_codes WHERE user_id = $1 AND used = FALSE",
                user_id,
            )
            await self._conn.execute(
                """
                INSERT INTO activation_codes (user_id, code, expires_at)
                VALUES ($1, $2, $3)
                """,
                user_id,
                code,
                expires_at,
            )

    async def get_valid(self, user_id: int, code: str) -> ActivationCode | None:
        """Return the code record if it is unused and not expired."""
        row = await self._conn.fetchrow(
            """
            SELECT id
            FROM activation_codes
            WHERE user_id   = $1
              AND code       = $2
              AND used       = FALSE
              AND expires_at > NOW()
            """,
            user_id,
            code,
        )
        if row is None:
            return None
        return ActivationCode(id=row["id"])

    async def mark_used(self, code_id: int) -> None:
        await self._conn.execute(
            "UPDATE activation_codes SET used = TRUE WHERE id = $1",
            code_id,
        )
