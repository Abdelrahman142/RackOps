from enum import Enum

from pydantic import BaseModel, Field


class RoomType(str, Enum):
    SERVER_ROOM = "SERVER_ROOM"
    NETWORK_ROOM = "NETWORK_ROOM"
    STORAGE_ROOM = "STORAGE_ROOM"
    UPS_ROOM = "UPS_ROOM"
    CONTROL_ROOM = "CONTROL_ROOM"
    OTHER = "OTHER"


class RoomStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    PLANNED = "PLANNED"
    OFFLINE = "OFFLINE"


class RoomCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Room name",
        examples=["Server Room A"],
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description=(
            "Unique code within floor"
        ),
        examples=["SR-A01"],
    )
    room_type: RoomType = Field(
        default=RoomType.SERVER_ROOM,
        description="Room type",
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Optional description",
    )
    status: RoomStatus = Field(
        default=RoomStatus.PLANNED,
        description="Current status",
    )
    area_sqm: float | None = Field(
        None,
        gt=0,
        description="Area in square meters",
    )
    height_meters: float | None = Field(
        None,
        gt=0,
        le=20.0,
        description="Ceiling height in meters",
    )
    max_rack_capacity: int | None = Field(
        None,
        gt=0,
        le=500,
        description="Maximum rack capacity",
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
    temperature_min: float | None = Field(
        None,
        ge=-20.0,
        le=60.0,
        description="Min operating temperature (C)",
    )
    temperature_max: float | None = Field(
        None,
        ge=-20.0,
        le=60.0,
        description="Max operating temperature (C)",
    )
    humidity_min: float | None = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Min operating humidity (%)",
    )
    humidity_max: float | None = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Max operating humidity (%)",
    )


class RoomUpdateRequest(BaseModel):
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
    room_type: RoomType | None = None
    description: str | None = Field(
        None,
        max_length=2000,
    )
    status: RoomStatus | None = None
    area_sqm: float | None = Field(
        None,
        gt=0,
    )
    height_meters: float | None = Field(
        None,
        gt=0,
        le=20.0,
    )
    max_rack_capacity: int | None = Field(
        None,
        gt=0,
        le=500,
    )
    max_power_capacity_kw: float | None = Field(
        None,
        gt=0,
    )
    max_cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
    )
    temperature_min: float | None = Field(
        None,
        ge=-20.0,
        le=60.0,
    )
    temperature_max: float | None = Field(
        None,
        ge=-20.0,
        le=60.0,
    )
    humidity_min: float | None = Field(
        None,
        ge=0.0,
        le=100.0,
    )
    humidity_max: float | None = Field(
        None,
        ge=0.0,
        le=100.0,
    )


class RoomResponse(BaseModel):
    id: str
    company_id: str
    floor_id: str
    name: str
    code: str
    room_type: str
    description: str | None
    status: str
    area_sqm: float | None
    height_meters: float | None
    max_rack_capacity: int | None
    max_power_capacity_kw: float | None
    max_cooling_capacity_kw: float | None
    temperature_min: float | None
    temperature_max: float | None
    humidity_min: float | None
    humidity_max: float | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RoomListResponse(BaseModel):
    rooms: list[RoomResponse]
    total: int
    page: int
    size: int
    pages: int
