from datetime import datetime

import asyncpg

from app.services.registration.exceptions import ExpiredCode, InvalidCode


class ActivationCodeRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def upsert(
        self, user_id: int, code: str, expires_at: datetime
    ) -> None:
        """Replace the existing code for this user, if any."""
        async with self._conn.transaction():
            await self._conn.execute(
                "DELETE FROM activation_codes WHERE user_id = $1",
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

    async def get_valid(self, user_id: int, code: str) -> None:
        """Raise InvalidCode or ExpiredCode if the code is not valid."""

        row = await self._conn.fetchrow(
            """
            SELECT id
            FROM activation_codes
            WHERE user_id   = $1
              AND code       = $2
              AND expires_at > NOW()
            """,
            user_id,
            code,
        )
        if row is None:
            expired = await self._conn.fetchrow(
                "SELECT id FROM activation_codes WHERE user_id = $1 AND code = $2",
                user_id,
                code,
            )
            if expired:
                raise ExpiredCode()
            raise InvalidCode(code)

    async def delete(self, user_id: int) -> None:
        await self._conn.execute(
            "DELETE FROM activation_codes WHERE user_id = $1",
            user_id,
        )
