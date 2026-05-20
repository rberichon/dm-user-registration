from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

LowercaseEmail = Annotated[EmailStr, AfterValidator(str.lower)]


class RegisterRequest(BaseModel):
    email: LowercaseEmail
    password: str = Field(min_length=8, description="Minimum 8 characters.")


class RegisterResponse(BaseModel):
    message: str


class ActivateRequest(BaseModel):
    code: str = Field(pattern=r"^\d{4}$", description="4-digit numeric code.")


class ActivateResponse(BaseModel):
    message: str
