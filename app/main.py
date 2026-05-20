import logging


from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
import secrets
import string
from datetime import datetime, timedelta, timezone


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Registration API")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    message: str


user_table = []
code_table = []


def hash_password(password: str) -> str:
    return "hashed_" + password


def generate_otp(length: int = 4) -> str:
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
    user_table.append({"email": email, "hashed_password": hashed, "active": False})

    code = generate_otp()
    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=60)

    code_table.append({"email": email, "code": code, "expires_at": expires_at})
    logger.info(
        f"Generated OTP {code} for {email}, expires at {expires_at.isoformat()}"
    )
    return RegisterResponse(
        message="Account created. Check your email to activate your account."
    )
