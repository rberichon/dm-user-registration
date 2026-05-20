from contextlib import asynccontextmanager
from datetime import datetime, timezone

from app.domain import DuplicateEmailError, User
from app.services.registration.exceptions import ExpiredCode, InvalidCode


class FakeUserRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._next_id = 1

    async def get_by_email(self, email: str) -> User | None:
        return self._users.get(email)

    async def create(self, email: str, hashed_password: str) -> int:
        if email in self._users:
            raise DuplicateEmailError(email)
        user = User(id=self._next_id, email=email, is_active=False)
        self._users[email] = user
        self._next_id += 1
        return user.id

    async def activate(self, user_id: int) -> None:
        for user in self._users.values():
            if user.id == user_id:
                user.is_active = True
                return

    @asynccontextmanager
    async def transaction(self):
        yield


class FakeActivationCodeRepository:
    def __init__(self) -> None:
        # user_id -> {"code", "expires_at"}
        self._codes: dict[int, dict] = {}

    async def upsert(
        self, user_id: int, code: str, expires_at: datetime
    ) -> None:
        self._codes[user_id] = {"code": code, "expires_at": expires_at}

    async def get_valid(self, user_id: int, code: str) -> None:
        entry = self._codes.get(user_id)
        if entry is None or entry["code"] != code:
            raise InvalidCode(code)
        if entry["expires_at"] < datetime.now(tz=timezone.utc):
            raise ExpiredCode()

    async def delete(self, user_id: int) -> None:
        self._codes.pop(user_id, None)

    def get_code_for_user(self, user_id: int) -> str | None:
        """Test helper: return the current OTP for a user."""
        entry = self._codes.get(user_id)
        return entry["code"] if entry else None

    def set_expires_at(self, user_id: int, expires_at: datetime) -> None:
        """Test helper: override the expiry of a user's code."""
        self._codes[user_id]["expires_at"] = expires_at
