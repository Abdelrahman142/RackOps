from enum import Enum

from pydantic import BaseModel, Field


class BuildingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
    PLANNED = "PLANNED"


class BuildingCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Building name",
        examples=["Main Building"],
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description=(
            "Unique code within datacenter"
        ),
        examples=["MB01"],
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Optional description",
    )
    status: BuildingStatus = Field(
        default=BuildingStatus.PLANNED,
        description="Current status",
    )
    address: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Building address",
        examples=["123 Data Center Blvd"],
    )
    number_of_floors: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Number of floors (1-100)",
    )
    total_area: float | None = Field(
        None,
        gt=0,
        description="Total area in sq meters",
    )
    power_capacity_kw: float | None = Field(
        None,
        gt=0,
        description="Power capacity in kW",
    )
    cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
        description="Cooling capacity in kW",
    )


class BuildingUpdateRequest(BaseModel):
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
    description: str | None = Field(
        None,
        max_length=2000,
    )
    status: BuildingStatus | None = None
    address: str | None = Field(
        None,
        min_length=1,
        max_length=500,
    )
    number_of_floors: int | None = Field(
        None,
        ge=1,
        le=100,
    )
    total_area: float | None = Field(
        None,
        gt=0,
    )
    power_capacity_kw: float | None = Field(
        None,
        gt=0,
    )
    cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
    )


class BuildingResponse(BaseModel):
    id: str
    company_id: str
    datacenter_id: str
    name: str
    code: str
    description: str | None
    status: str
    address: str
    number_of_floors: int
    total_area: float | None
    power_capacity_kw: float | None
    cooling_capacity_kw: float | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BuildingListResponse(BaseModel):
    buildings: list[BuildingResponse]
    total: int
    page: int
    size: int
    pages: int
