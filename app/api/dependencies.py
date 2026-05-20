from typing import Annotated

import asyncpg
from fastapi import Depends

from app.config import settings
from app.db.pool import get_db
from app.db.repositories.activation_codes import ActivationCodeRepository
from app.db.repositories.users import UserRepository
from app.third_party.mailpit import MailpitMailer

DbConn = Annotated[asyncpg.Connection, Depends(get_db)]


def get_user_repo(conn: DbConn) -> UserRepository:
    return UserRepository(conn)


def get_activation_code_repo(conn: DbConn) -> ActivationCodeRepository:
    return ActivationCodeRepository(conn)


def get_mailer() -> MailpitMailer:
    return MailpitMailer(settings.mail_service_url)


UserRepo = Annotated[UserRepository, Depends(get_user_repo)]
CodesRepo = Annotated[
    ActivationCodeRepository, Depends(get_activation_code_repo)
]
MailerDep = Annotated[MailpitMailer, Depends(get_mailer)]
