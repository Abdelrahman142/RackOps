from enum import Enum

from pydantic import BaseModel, Field


class DataCenterStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
    PLANNED = "PLANNED"


class DataCenterCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Data center name",
        examples=["US-East-1"],
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique code within company",
        examples=["USE1"],
    )
    country: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Country name",
        examples=["United States"],
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="City name",
        examples=["New York"],
    )
    address: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Full address",
        examples=["123 Data Center Blvd"],
    )
    timezone: str = Field(
        ...,
        max_length=50,
        description=(
            "IANA timezone identifier"
        ),
        examples=["America/New_York"],
    )
    status: DataCenterStatus = Field(
        default=DataCenterStatus.PLANNED,
        description="Current status",
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Optional description",
    )
    latitude: float | None = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Latitude (-90 to 90)",
    )
    longitude: float | None = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Longitude (-180 to 180)",
    )


class DataCenterUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    code: str | None = Field(
        None,
        min_length=1,
        max_length=50,
    )
    country: str | None = Field(
        None,
        min_length=1,
        max_length=100,
    )
    city: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    address: str | None = Field(
        None,
        min_length=1,
        max_length=500,
    )
    timezone: str | None = Field(
        None,
        max_length=50,
    )
    status: DataCenterStatus | None = None
    description: str | None = Field(
        None,
        max_length=2000,
    )
    latitude: float | None = Field(
        None,
        ge=-90.0,
        le=90.0,
    )
    longitude: float | None = Field(
        None,
        ge=-180.0,
        le=180.0,
    )


class DataCenterResponse(BaseModel):
    id: str
    company_id: str
    name: str
    code: str
    country: str
    city: str
    address: str
    timezone: str
    status: str
    description: str | None
    latitude: float | None
    longitude: float | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DataCenterListResponse(BaseModel):
    datacenters: list[DataCenterResponse]
    total: int
    page: int
    size: int
    pages: int
