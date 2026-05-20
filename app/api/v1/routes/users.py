import logging

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CodesRepo, CurrentUser, MailerDep, UserRepo
from app.api.v1.models import (
    ActivateRequest,
    ActivateResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services import registration
from app.services.registration import (
    AlreadyActive,
    EmailConflict,
    ExpiredCode,
    InvalidCode,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates an inactive user and sends a 4-digit OTP code "
        "valid for 60s to the provided email address."
    ),
)
async def register(
    body: RegisterRequest,
    users_repo: UserRepo,
    codes_repo: CodesRepo,
    mailer: MailerDep,
):
    try:
        await registration.register_user(
            body.email, body.password, users_repo, codes_repo, mailer
        )
    except EmailConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already in use.",
        )

    return RegisterResponse(
        message="Account created. Check your email to activate your account.",
    )


@router.post(
    "/activate",
    response_model=ActivateResponse,
    summary="Activate an account with the OTP code",
    description="Validates the 4-digit OTP code received by email. Requires Basic Auth.",
)
async def activate(
    body: ActivateRequest,
    current_user: CurrentUser,
    users_repo: UserRepo,
    codes_repo: CodesRepo,
    mailer: MailerDep,
):
    try:
        await registration.activate_user(
            current_user, body.code, users_repo, codes_repo, mailer
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
