from enum import Enum

from pydantic import BaseModel, Field


class PowerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WARNING = "WARNING"
    FAILED = "FAILED"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class PhaseType(str, Enum):
    SINGLE = "SINGLE"
    THREE_PHASE = "THREE_PHASE"


class FeedSourceType(str, Enum):
    UPS = "UPS"
    MAINS = "MAINS"


class FeedDestinationType(str, Enum):
    PDU = "PDU"
    RACK = "RACK"


class UPSCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="UPS name",
        examples=["UPS-A01"],
    )
    model: str | None = Field(
        None,
        max_length=255,
        description="UPS model",
        examples=["APC Smart-UPS 3000"],
    )
    manufacturer: str | None = Field(
        None,
        max_length=255,
        description="UPS manufacturer",
        examples=["APC"],
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
        description="Globally unique serial number",
    )
    status: PowerStatus = Field(
        default=PowerStatus.ACTIVE,
        description="Current status",
    )
    capacity_kva: float = Field(
        ...,
        gt=0,
        description="UPS capacity in kVA",
        examples=[3.0],
    )
    battery_capacity_minutes: int | None = Field(
        None,
        ge=0,
        description="Battery runtime in minutes",
        examples=[15],
    )
    input_voltage: float | None = Field(
        None,
        gt=0,
        description="Input voltage in V",
        examples=[208.0],
    )
    output_voltage: float | None = Field(
        None,
        gt=0,
        description="Output voltage in V",
        examples=[208.0],
    )
    efficiency_percent: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Efficiency percentage",
        examples=[95.0],
    )


class UPSUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    model: str | None = Field(
        None,
        max_length=255,
    )
    manufacturer: str | None = Field(
        None,
        max_length=255,
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
    )
    status: PowerStatus | None = None
    capacity_kva: float | None = Field(
        None,
        gt=0,
    )
    battery_capacity_minutes: int | None = Field(
        None,
        ge=0,
    )
    input_voltage: float | None = Field(
        None,
        gt=0,
    )
    output_voltage: float | None = Field(
        None,
        gt=0,
    )
    efficiency_percent: float | None = Field(
        None,
        ge=0,
        le=100,
    )


class UPSResponse(BaseModel):
    id: str
    company_id: str
    room_id: str
    name: str
    model: str | None
    manufacturer: str | None
    serial_number: str | None
    status: str
    capacity_kva: float
    battery_capacity_minutes: int | None
    input_voltage: float | None
    output_voltage: float | None
    efficiency_percent: float | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UPSListResponse(BaseModel):
    ups_systems: list[UPSResponse]
    total: int
    page: int
    size: int
    pages: int


class PDUCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="PDU name",
        examples=["PDU-A01"],
    )
    model: str | None = Field(
        None,
        max_length=255,
        description="PDU model",
    )
    manufacturer: str | None = Field(
        None,
        max_length=255,
        description="PDU manufacturer",
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
        description="Globally unique serial number",
    )
    status: PowerStatus = Field(
        default=PowerStatus.ACTIVE,
        description="Current status",
    )
    rack_id: str | None = Field(
        None,
        description="Associated rack ID (optional)",
    )
    total_capacity_amp: float = Field(
        ...,
        gt=0,
        description="Total capacity in amps",
        examples=[30.0],
    )
    current_usage_amp: float = Field(
        default=0,
        ge=0,
        description="Current usage in amps",
    )
    phase_type: PhaseType = Field(
        default=PhaseType.SINGLE,
        description="Phase type: SINGLE or THREE_PHASE",
    )


class PDUUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    model: str | None = Field(
        None,
        max_length=255,
    )
    manufacturer: str | None = Field(
        None,
        max_length=255,
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
    )
    status: PowerStatus | None = None
    rack_id: str | None = None
    total_capacity_amp: float | None = Field(
        None,
        gt=0,
    )
    current_usage_amp: float | None = Field(
        None,
        ge=0,
    )
    phase_type: PhaseType | None = None


class PDuresponse(BaseModel):
    id: str
    company_id: str
    room_id: str
    name: str
    model: str | None
    manufacturer: str | None
    serial_number: str | None
    status: str
    rack_id: str | None
    total_capacity_amp: float
    current_usage_amp: float
    phase_type: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PDUListResponse(BaseModel):
    pdus: list[PDuresponse]
    total: int
    page: int
    size: int
    pages: int


class PowerFeedCreateRequest(BaseModel):
    source_type: FeedSourceType = Field(
        ...,
        description="Source type: UPS or MAINS",
    )
    source_id: str = Field(
        ...,
        description="Source entity ID",
    )
    destination_type: FeedDestinationType = Field(
        ...,
        description="Destination type: PDU or RACK",
    )
    destination_id: str = Field(
        ...,
        description="Destination entity ID",
    )
    voltage: float = Field(
        ...,
        gt=0,
        description="Voltage in V",
        examples=[208.0],
    )
    amp_rating: float = Field(
        ...,
        gt=0,
        description="Amp rating",
        examples=[30.0],
    )
    status: PowerStatus = Field(
        default=PowerStatus.ACTIVE,
        description="Current status",
    )


class PowerFeedUpdateRequest(BaseModel):
    voltage: float | None = Field(
        None,
        gt=0,
    )
    amp_rating: float | None = Field(
        None,
        gt=0,
    )
    status: PowerStatus | None = None


class PowerFeedResponse(BaseModel):
    id: str
    company_id: str
    source_type: str
    source_id: str
    destination_type: str
    destination_id: str
    voltage: float
    amp_rating: float
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PowerFeedListResponse(BaseModel):
    power_feeds: list[PowerFeedResponse]
    total: int
    page: int
    size: int
    pages: int


class RackPowerResponse(BaseModel):
    rack_id: str
    rack_name: str
    power_capacity_kw: float | None
    allocated_power_kw: float
    available_power_kw: float | None
    power_usage_percentage: float | None
    device_power_watts: int
    pdus: list[dict]


class DevicePowerInfo(BaseModel):
    device_id: str
    device_name: str
    device_type: str
    power_consumption_watt: int | None


class RoomPowerSummaryResponse(BaseModel):
    room_id: str
    room_name: str
    total_ups_capacity_kva: float
    total_pdu_capacity_amp: float
    total_rack_power_capacity_kw: float | None
    total_device_power_watts: int
    ups_count: int
    pdu_count: int
    rack_count: int
    ups_details: list[dict]
    pdu_details: list[dict]


class DataCenterPowerSummaryResponse(BaseModel):
    datacenter_id: str
    datacenter_name: str
    total_ups_capacity_kva: float
    total_pdu_capacity_amp: float
    total_rack_power_capacity_kw: float | None
    total_device_power_watts: int
    room_count: int
    ups_count: int
    pdu_count: int
    rack_count: int
    room_summaries: list[dict]
