from typing import Annotated

import asyncpg
from fastapi import Depends

from app.db.pool import get_db
from app.db.repositories.activation_codes import ActivationCodeRepository
from app.db.repositories.users import UserRepository

DbConn = Annotated[asyncpg.Connection, Depends(get_db)]


def get_user_repo(conn: DbConn) -> UserRepository:
    return UserRepository(conn)


def get_activation_code_repo(conn: DbConn) -> ActivationCodeRepository:
    return ActivationCodeRepository(conn)


UserRepo = Annotated[UserRepository, Depends(get_user_repo)]
CodesRepo = Annotated[
    ActivationCodeRepository, Depends(get_activation_code_repo)
]
