from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    company_name: str = Field(
        ..., min_length=1, max_length=255
    )
    company_email: EmailStr
    name: str = Field(
        ..., min_length=1, max_length=255
    )
    email: EmailStr
    password: str = Field(
        ..., min_length=8, max_length=72
    )
    country: str | None = Field(
        None, max_length=100
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    company_id: str

    model_config = {"from_attributes": True}
