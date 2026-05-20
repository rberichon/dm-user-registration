from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Protocol

from app.domain import User


class IUserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def create(self, email: str, hashed_password: str) -> int: ...

    async def activate(self, user_id: int) -> None: ...

    def transaction(self) -> AbstractAsyncContextManager[None]: ...


class IActivationCodeRepository(Protocol):
    async def upsert(
        self, user_id: int, code: str, expires_at: datetime
    ) -> None: ...

    async def get_valid(self, user_id: int, code: str) -> None: ...

    async def delete(self, user_id: int) -> None: ...
