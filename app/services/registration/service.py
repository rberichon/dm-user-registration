import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from app.auth import hash_password

from .exceptions import (
    AlreadyActive,
    EmailConflict,
    ExpiredCode,
    InvalidCode,
    UserNotFound,
)

logger = logging.getLogger(__name__)


def _generate_otp(length: int = 4) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def _generate_new_validation_code(email) -> tuple[str, datetime]:
    code = _generate_otp()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=60)

    return code, expires_at


async def register_user(
    email: str,
    password: str,
    user_table: list[dict],
    code_table: list[dict],
):
    if any(user["email"] == email for user in user_table):
        raise EmailConflict(email)

    hashed = hash_password(password)
    user_table.append(
        {"email": email, "hashed_password": hashed, "active": False}
    )

    code, expires_at = _generate_new_validation_code(email)
    code_table.append({"email": email, "code": code, "expires_at": expires_at})
    # TODO use mail service
    logger.info(
        f"Generated OTP {code} for {email}, expires at {expires_at.isoformat()}"
    )


async def activate_user(
    email: str,
    code: str,
    user_table: list[dict],
    code_table: list[dict],
) -> None:
    user_code = None
    user_code_exp_at = None
    for entry in code_table:
        if entry["email"] == email:
            user_code = entry["code"]
            user_code_exp_at = entry["expires_at"]
    if not user_code:
        raise InvalidCode()

    user = None
    for entry in user_table:
        if entry["email"] == email:
            user = entry

    if not user:
        raise UserNotFound(email)

    if user["active"]:
        raise AlreadyActive(email)

    if user_code != code:
        raise InvalidCode()

    if user_code_exp_at and user_code_exp_at < datetime.now(tz=timezone.utc):
        code, expires_at = _generate_new_validation_code(email)
        # TODO use mail service
        logger.info(
            f"Generated OTP {code} for {email}, expires at {expires_at.isoformat()}"
        )

        raise ExpiredCode()

    user["active"] = True
