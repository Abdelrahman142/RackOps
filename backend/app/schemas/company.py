from pydantic import BaseModel, EmailStr, Field


class CompanyUpdateRequest(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=255
    )
    email: EmailStr | None = None
    country: str | None = Field(
        None, max_length=100
    )


class CompanyResponse(BaseModel):
    id: str
    name: str
    slug: str
    email: str
    country: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
