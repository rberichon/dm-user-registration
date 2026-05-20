from datetime import datetime, timedelta, timezone

VALID_EMAIL = "user@example.com"
VALID_PASSWORD = "secret123"


# ── Helpers ────────────────────────────────────────────────────────────────────


def _register(client, email=VALID_EMAIL, password=VALID_PASSWORD):
    return client.post(
        "/api/v1/users/register", json={"email": email, "password": password}
    )


def _get_otp(fake_users_repo, fake_codes_repo, email=VALID_EMAIL) -> str:
    user = fake_users_repo._users.get(email.lower())
    return fake_codes_repo.get_code_for_user(user.id)


def _activate(client, code, email=VALID_EMAIL, password=VALID_PASSWORD):
    return client.post(
        "/api/v1/users/activate",
        json={"code": code},
        auth=(email, password),
    )


# ── POST /api/v1/users/register ────────────────────────────────────────────────


def test_register_success(client):
    response = _register(client)
    assert response.status_code == 201
    assert "message" in response.json()


def test_register_creates_inactive_user(client, fake_users_repo):
    _register(client)
    user = fake_users_repo._users.get(VALID_EMAIL)
    assert user is not None
    assert user.is_active is False


def test_register_duplicate_email_returns_409(client):
    _register(client)
    response = _register(client)
    assert response.status_code == 409


def test_register_invalid_email_returns_422(client):
    response = client.post(
        "/api/v1/users/register",
        json={"email": "not-an-email", "password": VALID_PASSWORD},
    )
    assert response.status_code == 422


def test_register_password_too_short_returns_422(client):
    response = client.post(
        "/api/v1/users/register",
        json={"email": VALID_EMAIL, "password": "short"},
    )
    assert response.status_code == 422


def test_register_normalizes_email_to_lowercase(client):
    _register(client, email="USER@EXAMPLE.COM")
    response = _register(client, email="user@example.com")
    assert response.status_code == 409


def test_register_sends_activation_email(client, fake_mailer):
    _register(client)
    assert len(fake_mailer.sent) == 1
    assert fake_mailer.sent[0]["email"] == VALID_EMAIL


# ── POST /api/v1/users/activate ────────────────────────────────────────────────


def test_activate_success(client, fake_users_repo, fake_codes_repo):
    _register(client)
    code = _get_otp(fake_users_repo, fake_codes_repo)
    response = _activate(client, code)
    assert response.status_code == 200
    assert "message" in response.json()


def test_activate_marks_user_as_active(
    client, fake_users_repo, fake_codes_repo
):
    _register(client)
    code = _get_otp(fake_users_repo, fake_codes_repo)
    _activate(client, code)
    assert fake_users_repo._users[VALID_EMAIL].is_active is True


def test_activate_invalid_credentials_returns_401(client):
    _register(client)
    response = client.post(
        "/api/v1/users/activate",
        json={"code": "1234"},
        auth=(VALID_EMAIL, "wrongpassword"),
    )
    assert response.status_code == 401


def test_activate_unknown_user_returns_401(client):
    response = client.post(
        "/api/v1/users/activate",
        json={"code": "1234"},
        auth=("ghost@example.com", "whatever"),
    )
    assert response.status_code == 401


def test_activate_wrong_code_returns_400(
    client, fake_users_repo, fake_codes_repo
):
    _register(client)
    code = _get_otp(fake_users_repo, fake_codes_repo)
    wrong_code = "0000" if code != "0000" else "1111"
    response = _activate(client, wrong_code)
    assert response.status_code == 400


def test_activate_already_active_returns_400(
    client, fake_users_repo, fake_codes_repo
):
    _register(client)
    code = _get_otp(fake_users_repo, fake_codes_repo)
    _activate(client, code)
    response = _activate(client, code)
    assert response.status_code == 400


def test_activate_expired_code_returns_400(
    client, fake_users_repo, fake_codes_repo
):
    _register(client)
    user = fake_users_repo._users[VALID_EMAIL]
    fake_codes_repo.set_expires_at(
        user.id, datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    )
    code = fake_codes_repo.get_code_for_user(user.id)
    response = _activate(client, code)
    assert response.status_code == 400


def test_activate_expired_code_resends_email(
    client, fake_users_repo, fake_codes_repo, fake_mailer
):
    _register(client)
    user = fake_users_repo._users[VALID_EMAIL]
    fake_codes_repo.set_expires_at(
        user.id, datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    )
    code = fake_codes_repo.get_code_for_user(user.id)
    _activate(client, code)
    assert len(fake_mailer.sent) == 2  # initial registration + resend


def test_activate_invalid_code_format_returns_422(client):
    _register(client)
    response = client.post(
        "/api/v1/users/activate",
        json={"code": "abcd"},
        auth=(VALID_EMAIL, VALID_PASSWORD),
    )
    assert response.status_code == 422
