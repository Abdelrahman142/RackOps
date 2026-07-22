from enum import Enum

from pydantic import BaseModel, Field


class RackType(str, Enum):
    SERVER_RACK = "SERVER_RACK"
    NETWORK_RACK = "NETWORK_RACK"
    STORAGE_RACK = "STORAGE_RACK"
    OPEN_FRAME_RACK = "OPEN_FRAME_RACK"
    CUSTOM = "CUSTOM"


class RackStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FULL = "FULL"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
    DECOMMISSIONED = "DECOMMISSIONED"


class RackCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Rack name",
        examples=["Rack-A01"],
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description=(
            "Unique code within room"
        ),
        examples=["RK-A01"],
    )
    rack_type: RackType = Field(
        default=RackType.SERVER_RACK,
        description="Rack type",
    )
    status: RackStatus = Field(
        default=RackStatus.ACTIVE,
        description="Current status",
    )
    height_units: int = Field(
        default=42,
        ge=1,
        le=52,
        description="Height in rack units (U)",
    )
    width_mm: float | None = Field(
        None,
        gt=0,
        description="Width in millimeters",
    )
    depth_mm: float | None = Field(
        None,
        gt=0,
        description="Depth in millimeters",
    )
    max_weight_kg: float | None = Field(
        None,
        gt=0,
        description="Max weight capacity in kg",
    )
    current_weight_kg: float | None = Field(
        default=0,
        ge=0,
        description="Current weight in kg",
    )
    power_capacity_kw: float | None = Field(
        None,
        gt=0,
        description="Power capacity in kW",
    )
    current_power_usage_kw: float | None = Field(
        default=0,
        ge=0,
        description="Current power usage in kW",
    )
    cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
        description="Cooling capacity in kW",
    )
    manufacturer: str | None = Field(
        None,
        max_length=255,
        description="Rack manufacturer",
    )
    model: str | None = Field(
        None,
        max_length=255,
        description="Rack model",
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
        description="Unique serial number",
    )
    position_in_room: int | None = Field(
        None,
        ge=0,
        description="Position within room",
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Optional description",
    )


class RackUpdateRequest(BaseModel):
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
    rack_type: RackType | None = None
    status: RackStatus | None = None
    height_units: int | None = Field(
        None,
        ge=1,
        le=52,
    )
    width_mm: float | None = Field(
        None,
        gt=0,
    )
    depth_mm: float | None = Field(
        None,
        gt=0,
    )
    max_weight_kg: float | None = Field(
        None,
        gt=0,
    )
    current_weight_kg: float | None = Field(
        None,
        ge=0,
    )
    power_capacity_kw: float | None = Field(
        None,
        gt=0,
    )
    current_power_usage_kw: float | None = Field(
        None,
        ge=0,
    )
    cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
    )
    manufacturer: str | None = Field(
        None,
        max_length=255,
    )
    model: str | None = Field(
        None,
        max_length=255,
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
    )
    position_in_room: int | None = Field(
        None,
        ge=0,
    )
    description: str | None = Field(
        None,
        max_length=2000,
    )


class RackResponse(BaseModel):
    id: str
    company_id: str
    room_id: str
    name: str
    code: str
    rack_type: str
    status: str
    height_units: int
    width_mm: float | None
    depth_mm: float | None
    max_weight_kg: float | None
    current_weight_kg: float | None
    power_capacity_kw: float | None
    current_power_usage_kw: float | None
    cooling_capacity_kw: float | None
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    position_in_room: int | None
    description: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RackListResponse(BaseModel):
    racks: list[RackResponse]
    total: int
    page: int
    size: int
    pages: int


class RackCapacityResponse(BaseModel):
    total_u: int
    used_u: int
    available_u: int
    power_capacity_kw: float | None
    used_power_kw: float
    available_power_kw: float | None
    weight_capacity_kg: float | None
    used_weight_kg: float
    available_weight_kg: float | None
