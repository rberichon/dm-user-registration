import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_activation_code_repo, get_user_repo
from app.main import app
from tests.fakes import FakeActivationCodeRepository, FakeUserRepository


@pytest.fixture
def client():
    fake_users_repo = FakeUserRepository()
    fake_codes_repo = FakeActivationCodeRepository()

    app.dependency_overrides[get_user_repo] = lambda: fake_users_repo
    app.dependency_overrides[get_activation_code_repo] = lambda: fake_codes_repo

    yield TestClient(app), fake_users_repo, fake_codes_repo

    app.dependency_overrides.clear()
