from typing import Annotated

import pytest
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_activation_code_repo,
    get_current_user,
    get_mailer,
    get_user_repo,
)
from app.auth import verify_password
from app.domain import User
from app.main import app
from tests.fakes import (
    FakeActivationCodeRepository,
    FakeMailer,
    FakeUserRepository,
)

_http_basic = HTTPBasic()


@pytest.fixture
def fake_users_repo():
    return FakeUserRepository()


@pytest.fixture
def fake_codes_repo():
    return FakeActivationCodeRepository()


@pytest.fixture
def fake_mailer():
    return FakeMailer()


@pytest.fixture
def client(fake_users_repo, fake_codes_repo, fake_mailer):
    async def _fake_get_current_user(
        credentials: Annotated[HTTPBasicCredentials, Depends(_http_basic)],
    ) -> User:
        user = await fake_users_repo.get_by_email(credentials.username)
        if user is None or not verify_password(
            credentials.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
                headers={"WWW-Authenticate": "Basic"},
            )
        return user

    app.dependency_overrides[get_user_repo] = lambda: fake_users_repo
    app.dependency_overrides[get_activation_code_repo] = lambda: fake_codes_repo
    app.dependency_overrides[get_mailer] = lambda: fake_mailer
    app.dependency_overrides[get_current_user] = _fake_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()
