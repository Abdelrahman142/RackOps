from enum import Enum

from pydantic import BaseModel, Field


class FloorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    PLANNED = "PLANNED"
    OFFLINE = "OFFLINE"


class FloorCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Floor name",
        examples=["Ground Floor"],
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description=(
            "Unique code within building"
        ),
        examples=["GF01"],
    )
    floor_number: int = Field(
        ...,
        ge=-5,
        le=100,
        description=(
            "Unique floor number within building. "
            "Negative for basement levels."
        ),
        examples=[0],
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Optional description",
    )
    status: FloorStatus = Field(
        default=FloorStatus.PLANNED,
        description="Current status",
    )
    total_area_sqm: float | None = Field(
        None,
        gt=0,
        description="Total area in square meters",
    )
    max_power_capacity_kw: float | None = Field(
        None,
        gt=0,
        description="Max power capacity in kW",
    )
    max_cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
        description="Max cooling capacity in kW",
    )


class FloorUpdateRequest(BaseModel):
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
    floor_number: int | None = Field(
        None,
        ge=-5,
        le=100,
    )
    description: str | None = Field(
        None,
        max_length=2000,
    )
    status: FloorStatus | None = None
    total_area_sqm: float | None = Field(
        None,
        gt=0,
    )
    max_power_capacity_kw: float | None = Field(
        None,
        gt=0,
    )
    max_cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
    )


class FloorResponse(BaseModel):
    id: str
    company_id: str
    building_id: str
    name: str
    code: str
    floor_number: int
    description: str | None
    status: str
    total_area_sqm: float | None
    max_power_capacity_kw: float | None
    max_cooling_capacity_kw: float | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class FloorListResponse(BaseModel):
    floors: list[FloorResponse]
    total: int
    page: int
    size: int
    pages: int
