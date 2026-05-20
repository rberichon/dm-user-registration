import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from app.auth import hash_password
from app.domain import DuplicateEmailError

from .exceptions import (
    AlreadyActive,
    EmailConflict,
    ExpiredCode,
    InvalidCode,
    UserNotFound,
)
from .interfaces import IActivationCodeRepository, IUserRepository

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
    users_repo: IUserRepository,
    codes_repo: IActivationCodeRepository,
):
    hashed = hash_password(password)

    try:
        user_id = await users_repo.create(email, hashed)
    except DuplicateEmailError:
        raise EmailConflict(email)

    code, expires_at = _generate_new_validation_code(email)
    await codes_repo.upsert(user_id, code, expires_at)

    # TODO use mail service
    logger.info(
        f"Generated OTP {code} for {email}, expires at {expires_at.isoformat()}"
    )


async def activate_user(
    email: str,
    code: str,
    users_repo: IUserRepository,
    codes_repo: IActivationCodeRepository,
) -> None:
    user = await users_repo.get_by_email(email)
    if not user:
        raise UserNotFound(email)

    if user.is_active:
        raise AlreadyActive(email)

    try:
        await codes_repo.get_valid(user.id, code)
    except InvalidCode:
        raise InvalidCode(code)
    except ExpiredCode:
        new_code, expires_at = _generate_new_validation_code(email)
        await codes_repo.upsert(user.id, new_code, expires_at)
        # TODO use mail service
        logger.info(
            f"Generated OTP {new_code} for {email}, expires at {expires_at.isoformat()}"
        )
        raise ExpiredCode

    async with users_repo.transaction():
        await codes_repo.delete(user.id)
        await users_repo.activate(user.id)
