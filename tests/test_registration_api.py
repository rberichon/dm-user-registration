from datetime import datetime, timedelta, timezone

import app.main as main_module

VALID_EMAIL = "user@example.com"
VALID_PASSWORD = "secret123"


# ── Helpers ────────────────────────────────────────────────────────────────────


def _register(client, email=VALID_EMAIL, password=VALID_PASSWORD):
    return client.post(
        "/api/v1/users/register", json={"email": email, "password": password}
    )


def _get_otp(email=VALID_EMAIL) -> str:
    entry = next(
        e for e in main_module.code_table if e["email"] == email.lower()
    )
    return entry["code"]


def _register_and_get_otp(
    client, email=VALID_EMAIL, password=VALID_PASSWORD
) -> str:
    _register(client, email, password)
    return _get_otp(email)


# ── POST /api/v1/users/register ────────────────────────────────────────────────


def test_register_success(client):
    response = _register(client)
    assert response.status_code == 201
    assert "message" in response.json()


def test_register_creates_inactive_user(client):
    _register(client)
    user = next(u for u in main_module.user_table if u["email"] == VALID_EMAIL)
    assert user["active"] is False


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


# ── POST /api/v1/users/activate ────────────────────────────────────────────────


def test_activate_success(client):
    code = _register_and_get_otp(client)
    response = client.post(
        "/api/v1/users/activate", json={"email": VALID_EMAIL, "code": code}
    )
    assert response.status_code == 200
    assert "message" in response.json()


def test_activate_marks_user_as_active(client):
    code = _register_and_get_otp(client)
    client.post(
        "/api/v1/users/activate", json={"email": VALID_EMAIL, "code": code}
    )
    user = next(u for u in main_module.user_table if u["email"] == VALID_EMAIL)
    assert user["active"] is True


def test_activate_no_code_for_email_returns_400(client):
    response = client.post(
        "/api/v1/users/activate",
        json={"email": "ghost@example.com", "code": "1234"},
    )
    assert response.status_code == 400


def test_activate_no_user_for_code_returns_404(client):
    # Orphaned code with no corresponding user — UserNotFound branch in service
    main_module.code_table.append({
        "email": VALID_EMAIL,
        "code": "1234",
        "expires_at": datetime.now(tz=timezone.utc) + timedelta(seconds=60),
    })
    response = client.post(
        "/api/v1/users/activate", json={"email": VALID_EMAIL, "code": "1234"}
    )
    assert response.status_code == 404


def test_activate_wrong_code_returns_400(client):
    code = _register_and_get_otp(client)
    wrong_code = "0000" if code != "0000" else "1111"
    response = client.post(
        "/api/v1/users/activate",
        json={"email": VALID_EMAIL, "code": wrong_code},
    )
    assert response.status_code == 400


def test_activate_already_active_returns_400(client):
    code = _register_and_get_otp(client)
    client.post(
        "/api/v1/users/activate", json={"email": VALID_EMAIL, "code": code}
    )
    response = client.post(
        "/api/v1/users/activate", json={"email": VALID_EMAIL, "code": code}
    )
    assert response.status_code == 400


def test_activate_expired_code_returns_400(client):
    code = _register_and_get_otp(client)
    entry = next(e for e in main_module.code_table if e["email"] == VALID_EMAIL)
    entry["expires_at"] = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    response = client.post(
        "/api/v1/users/activate", json={"email": VALID_EMAIL, "code": code}
    )
    assert response.status_code == 400


def test_activate_invalid_code_format_returns_422(client):
    response = client.post(
        "/api/v1/users/activate", json={"email": VALID_EMAIL, "code": "abcd"}
    )
    assert response.status_code == 422
