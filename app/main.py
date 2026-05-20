import logging


from fastapi import FastAPI, HTTPException, status

from app.services.registration import (
    AlreadyActive,
    EmailConflict,
    InvalidCode,
    UserNotFound,
)

from app.api.v1.models import (
    ActivateRequest,
    ActivateResponse,
    RegisterRequest,
    RegisterResponse,
)

from app.services import registration
from app.services.registration.exceptions import ExpiredCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="User Registration API")


user_table = []  # {"email": mail@mail.com, "active": False, "password": "hashedpwd"}
code_table = []  # {"email": mail@mail.com, "code": 1234, "expires_at": "datetime object"}


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
    try:
        await registration.register_user(
            body.email, body.password, user_table, code_table
        )
    except EmailConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already in use.",
        )

    return RegisterResponse(
        message="Account created. Check your email to activate your account.",
    )


@app.post(
    "/api/v1/users/activate",
    response_model=ActivateResponse,
    summary="Activate an account with the OTP code",
    description="Validates the 4-digit code received by email to activate the account.",
)
async def activate(body: ActivateRequest):
    try:
        await registration.activate_user(
            body.email, body.code, user_table, code_table
        )
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    except AlreadyActive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is already active.",
        )
    except InvalidCode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code.",
        )
    except ExpiredCode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expired code. A new code has been sent to your email account.",
        )

    return ActivateResponse(message="Account successfully activated.")
