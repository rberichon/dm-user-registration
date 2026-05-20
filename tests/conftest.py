import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_activation_code_repo, get_mailer, get_user_repo
from app.main import app
from tests.fakes import FakeActivationCodeRepository, FakeMailer, FakeUserRepository


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
    app.dependency_overrides[get_user_repo] = lambda: fake_users_repo
    app.dependency_overrides[get_activation_code_repo] = lambda: fake_codes_repo
    app.dependency_overrides[get_mailer] = lambda: fake_mailer
    yield TestClient(app)
    app.dependency_overrides.clear()
