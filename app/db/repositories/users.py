import asyncpg
from asyncpg.exceptions import UniqueViolationError

from app.domain import DuplicateEmailError, User


class UserRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def get_by_email(self, email: str) -> User | None:
        row = await self._conn.fetchrow(
            "SELECT id, email, is_active FROM users WHERE email = $1",
            email,
        )
        if row is None:
            return None
        return User(
            id=row["id"], email=row["email"], is_active=row["is_active"]
        )

    async def create(self, email: str, hashed_password: str) -> int:
        try:
            row = await self._conn.fetchrow(
                """
                INSERT INTO users (email, password)
                VALUES ($1, $2)
                RETURNING id
                """,
                email,
                hashed_password,
            )
        except UniqueViolationError as exc:
            raise DuplicateEmailError(email) from exc
        return row["id"]

    async def activate(self, user_id: int) -> None:
        await self._conn.execute(
            "UPDATE users SET is_active = TRUE WHERE id = $1",
            user_id,
        )

    def transaction(self):
        return self._conn.transaction()
