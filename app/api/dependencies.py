from typing import Annotated

import asyncpg
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.auth import verify_password
from app.config import settings
from app.db.pool import get_db
from app.db.repositories.activation_codes import ActivationCodeRepository
from app.db.repositories.users import UserRepository
from app.domain import User
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

_http_basic = HTTPBasic()


async def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(_http_basic)],
    users_repo: UserRepo,
) -> User:
    user = await users_repo.get_by_email(credentials.username)
    if user is None or not verify_password(
        credentials.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
