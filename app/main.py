import logging


from fastapi import FastAPI, HTTPException, status
import secrets
import string
from datetime import datetime, timedelta, timezone

from app.api.v1.models import (
    ActivateRequest,
    ActivateResponse,
    RegisterRequest,
    RegisterResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Registration API")


user_table = []  # {"email": mail@mail.com, "active": False, "password": "hashedpwd"}
code_table = []  # {"email": mail@mail.com, "code": 1234, "expires_at": "datetime object"}


def hash_password(password: str) -> str:
    return "hashed_" + password


def generate_otp(length: int = 4) -> int:
    return "".join(secrets.choice(string.digits) for _ in range(length))


@app.post(
    "/api/v1/users/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Regiser a new user",
    description=(
        "Creates an inactive user and sends a 4-digit OTP code "
        "valid for 60s to the provided email address."
    ),
)
async def register(body: RegisterRequest):
    email = body.email.lower()
    if any(user["email"] == email for user in user_table):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already in use.",
        )

    hashed = hash_password(body.password)
    user_table.append(
        {"email": email, "hashed_password": hashed, "active": False}
    )

    code = generate_otp()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=60)

    code_table.append({"email": email, "code": code, "expires_at": expires_at})
    logger.info(
        f"Generated OTP {code} for {email}, expires at {expires_at.isoformat()}"
    )
    return RegisterResponse(
        message="Account created. Check your email to activate your account."
    )


@app.post(
    "/api/v1/users/activate",
    response_model=ActivateResponse,
    summary="Activate an account with the OTP code",
    description="Validates the 4-digit code received by email to activate the account.",
)
async def activate(body: ActivateRequest):
    email = body.email.lower()

    user_code = None
    user_code_exp_at = None
    for entry in code_table:
        if entry["email"] == email:
            user_code = entry["code"]
            user_code_exp_at = entry["expires_at"]
    if not user_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown user",
        )

    user = None
    for entry in user_table:
        if entry["email"] == email:
            user = entry

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown user",
        )

    if user["active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already active",
        )

    if user_code != body.code:
        print(user_code, body.code)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code.",
        )

    if user_code_exp_at and user_code_exp_at < datetime.now(tz=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code expired.",
        )

    user["active"] = True

    return ActivateResponse(message="Account successfully activated.")
