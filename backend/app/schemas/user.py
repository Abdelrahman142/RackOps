from pydantic import BaseModel, EmailStr, Field

VALID_ROLES = ["OWNER", "ADMIN", "ENGINEER", "VIEWER"]


class UserCreateRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255
    )
    email: EmailStr
    password: str = Field(
        ..., min_length=8, max_length=72
    )
    role: str = Field(
        default="VIEWER",
        pattern=r"^(ADMIN|ENGINEER|VIEWER)$",
    )


class UserUpdateRequest(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=255
    )
    role: str | None = Field(
        None,
        pattern=r"^(OWNER|ADMIN|ENGINEER|VIEWER)$",
    )


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=255
    )
    current_password: str | None = None
    new_password: str | None = Field(
        None, min_length=8, max_length=72
    )


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    company_id: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
