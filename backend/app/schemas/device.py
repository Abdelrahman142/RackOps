from enum import Enum

from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    SERVER = "SERVER"
    SWITCH = "SWITCH"
    ROUTER = "ROUTER"
    FIREWALL = "FIREWALL"
    STORAGE = "STORAGE"
    UPS = "UPS"
    PDU = "PDU"
    LOAD_BALANCER = "LOAD_BALANCER"
    PATCH_PANEL = "PATCH_PANEL"
    OTHER = "OTHER"


class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    FAILED = "FAILED"
    DECOMMISSIONED = "DECOMMISSIONED"


class DeviceCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Device name (unique within company)",
        examples=["web-server-01"],
    )
    hostname: str | None = Field(
        None,
        max_length=255,
        description="Network hostname",
        examples=["web01.prod.example.com"],
    )
    device_type: DeviceType = Field(
        default=DeviceType.SERVER,
        description="Device type",
    )
    status: DeviceStatus = Field(
        default=DeviceStatus.ACTIVE,
        description="Current status",
    )
    vendor: str | None = Field(
        None,
        max_length=255,
        description="Device vendor/manufacturer",
        examples=["Dell"],
    )
    model: str | None = Field(
        None,
        max_length=255,
        description="Device model",
        examples=["PowerEdge R750"],
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
        description="Globally unique serial number",
        examples=["SN-DEL-2024-001"],
    )
    asset_tag: str | None = Field(
        None,
        max_length=255,
        description="Unique asset tag for tracking",
        examples=["IT-ASSET-001"],
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Optional description",
    )
    rack_unit_start: int | None = Field(
        None,
        ge=1,
        le=52,
        description="Starting rack unit position (1-based from bottom)",
        examples=[1],
    )
    rack_unit_height: int = Field(
        default=1,
        ge=1,
        le=42,
        description="Height in rack units",
    )
    front_or_rear: str | None = Field(
        None,
        description="Mounting position: FRONT or REAR",
        examples=["FRONT"],
    )
    ip_address: str | None = Field(
        None,
        max_length=45,
        description="Primary IP address",
        examples=["192.168.1.100"],
    )
    mac_address: str | None = Field(
        None,
        max_length=17,
        description="MAC address",
        examples=["AA:BB:CC:DD:EE:FF"],
    )
    management_ip: str | None = Field(
        None,
        max_length=45,
        description="Out-of-band management IP",
        examples=["10.0.0.100"],
    )
    operating_system: str | None = Field(
        None,
        max_length=255,
        description="Operating system",
        examples=["Ubuntu 22.04 LTS"],
    )
    cpu: str | None = Field(
        None,
        max_length=255,
        description="CPU specification",
        examples=["2x Intel Xeon Gold 6348"],
    )
    memory_gb: int | None = Field(
        None,
        ge=0,
        description="RAM in GB",
        examples=[256],
    )
    storage_gb: int | None = Field(
        None,
        ge=0,
        description="Storage in GB",
        examples=[2000],
    )
    power_consumption_watt: int | None = Field(
        None,
        ge=0,
        description="Power consumption in watts",
        examples=[750],
    )
    purchase_date: str | None = Field(
        None,
        max_length=10,
        description="Purchase date (YYYY-MM-DD)",
        examples=["2024-01-15"],
    )
    warranty_end_date: str | None = Field(
        None,
        max_length=10,
        description="Warranty end date (YYYY-MM-DD)",
        examples=["2027-01-15"],
    )


class DeviceUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    hostname: str | None = Field(
        None,
        max_length=255,
    )
    device_type: DeviceType | None = None
    status: DeviceStatus | None = None
    vendor: str | None = Field(
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
    asset_tag: str | None = Field(
        None,
        max_length=255,
    )
    description: str | None = Field(
        None,
        max_length=2000,
    )
    rack_unit_start: int | None = Field(
        None,
        ge=1,
        le=52,
    )
    rack_unit_height: int | None = Field(
        None,
        ge=1,
        le=42,
    )
    front_or_rear: str | None = Field(
        None,
        max_length=10,
    )
    ip_address: str | None = Field(
        None,
        max_length=45,
    )
    mac_address: str | None = Field(
        None,
        max_length=17,
    )
    management_ip: str | None = Field(
        None,
        max_length=45,
    )
    operating_system: str | None = Field(
        None,
        max_length=255,
    )
    cpu: str | None = Field(
        None,
        max_length=255,
    )
    memory_gb: int | None = Field(
        None,
        ge=0,
    )
    storage_gb: int | None = Field(
        None,
        ge=0,
    )
    power_consumption_watt: int | None = Field(
        None,
        ge=0,
    )
    purchase_date: str | None = Field(
        None,
        max_length=10,
    )
    warranty_end_date: str | None = Field(
        None,
        max_length=10,
    )


class DeviceResponse(BaseModel):
    id: str
    company_id: str
    rack_id: str
    name: str
    hostname: str | None
    device_type: str
    status: str
    vendor: str | None
    model: str | None
    serial_number: str | None
    asset_tag: str | None
    description: str | None
    rack_unit_start: int | None
    rack_unit_height: int
    front_or_rear: str | None
    ip_address: str | None
    mac_address: str | None
    management_ip: str | None
    operating_system: str | None
    cpu: str | None
    memory_gb: int | None
    storage_gb: int | None
    power_consumption_watt: int | None
    purchase_date: str | None
    warranty_end_date: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]
    total: int
    page: int
    size: int
    pages: int


class RackUnitPosition(BaseModel):
    unit: int
    occupied: bool
    device_id: str | None = None
    device_name: str | None = None
    device_type: str | None = None


class RackLayoutResponse(BaseModel):
    rack_id: str
    rack_name: str
    total_units: int
    used_units: int
    available_units: int
    positions: list[RackUnitPosition]


class CheckPlacementRequest(BaseModel):
    rack_unit_start: int = Field(
        ...,
        ge=1,
        le=52,
        description="Starting rack unit position",
    )
    rack_unit_height: int = Field(
        ...,
        ge=1,
        le=42,
        description="Height in rack units",
    )
    device_id: str | None = Field(
        None,
        description=(
            "Device ID to exclude (for updates)"
        ),
    )


class CheckPlacementResponse(BaseModel):
    fits: bool
    reason: str
    rack_unit_start: int
    rack_unit_height: int
    overlapping_devices: list[dict]
