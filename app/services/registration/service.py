import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from app.auth import hash_password
from app.domain import DuplicateEmailError, User

from .exceptions import AlreadyActive, EmailConflict, ExpiredCode, InvalidCode
from .interfaces import IActivationCodeRepository, IMailer, IUserRepository

logger = logging.getLogger(__name__)


def _generate_otp(length: int = 4) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def _generate_new_validation_code() -> tuple[str, datetime]:
    code = _generate_otp()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=60)
    return code, expires_at


async def register_user(
    email: str,
    password: str,
    users_repo: IUserRepository,
    codes_repo: IActivationCodeRepository,
    mailer: IMailer,
):
    hashed = hash_password(password)

    try:
        user_id = await users_repo.create(email, hashed)
    except DuplicateEmailError:
        raise EmailConflict(email)

    code, expires_at = _generate_new_validation_code()
    await codes_repo.upsert(user_id, code, expires_at)

    logger.info("otp_generated email=%s expires_at=%s", email, expires_at.isoformat())
    await mailer.send_activation_code(email, code)
    logger.info("user_registered email=%s", email)


async def activate_user(
    user: User,
    code: str,
    users_repo: IUserRepository,
    codes_repo: IActivationCodeRepository,
    mailer: IMailer,
) -> None:
    if user.is_active:
        raise AlreadyActive(user.email)

    try:
        await codes_repo.get_valid(user.id, code)
    except InvalidCode:
        raise InvalidCode(code)
    except ExpiredCode:
        new_code, expires_at = _generate_new_validation_code()
        await codes_repo.upsert(user.id, new_code, expires_at)
        logger.info(
            "otp_regenerated email=%s expires_at=%s",
            user.email,
            expires_at.isoformat(),
        )
        await mailer.send_activation_code(user.email, new_code)
        raise ExpiredCode

    async with users_repo.transaction():
        await codes_repo.delete(user.id)
        await users_repo.activate(user.id)

    logger.info("user_activated email=%s", user.email)
