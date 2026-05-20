from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters.")


class RegisterResponse(BaseModel):
    message: str


class ActivateRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{4}$", description="4-digit numeric code.")


class ActivateResponse(BaseModel):
    message: str
