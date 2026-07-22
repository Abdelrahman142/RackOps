from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CoolingUnitType(str, Enum):
    CRAC = "CRAC"
    CRAH = "CRAH"
    CHILLER = "CHILLER"
    FAN_WALL = "FAN_WALL"
    OTHER = "OTHER"


class CoolingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WARNING = "WARNING"
    FAILED = "FAILED"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"


class SensorType(str, Enum):
    TEMPERATURE = "TEMPERATURE"
    HUMIDITY = "HUMIDITY"
    POWER = "POWER"
    AIRFLOW = "AIRFLOW"
    SMOKE = "SMOKE"
    WATER_LEAK = "WATER_LEAK"
    OTHER = "OTHER"


class HealthStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class CoolingUnitCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Cooling unit name",
        examples=["CRAC-A01"],
    )
    manufacturer: str | None = Field(
        None,
        max_length=255,
        description="Cooling unit manufacturer",
        examples=["Liebert"],
    )
    model: str | None = Field(
        None,
        max_length=255,
        description="Cooling unit model",
        examples=["Liebert DFS"],
    )
    serial_number: str | None = Field(
        None,
        max_length=255,
        description="Globally unique serial number",
    )
    type: CoolingUnitType = Field(
        default=CoolingUnitType.CRAC,
        description="Cooling unit type",
    )
    status: CoolingStatus = Field(
        default=CoolingStatus.ACTIVE,
        description="Current status",
    )
    cooling_capacity_kw: float = Field(
        ...,
        gt=0,
        description="Cooling capacity in kW",
        examples=[10.0],
    )
    airflow_cfm: float | None = Field(
        None,
        ge=0,
        description="Airflow in CFM",
        examples=[2000.0],
    )
    power_consumption_kw: float | None = Field(
        None,
        ge=0,
        description="Power consumption in kW",
        examples=[3.5],
    )


class CoolingUnitUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
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
    type: CoolingUnitType | None = None
    status: CoolingStatus | None = None
    cooling_capacity_kw: float | None = Field(
        None,
        gt=0,
    )
    airflow_cfm: float | None = Field(
        None,
        ge=0,
    )
    power_consumption_kw: float | None = Field(
        None,
        ge=0,
    )


class CoolingUnitResponse(BaseModel):
    id: str
    company_id: str
    room_id: str
    name: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    type: str
    status: str
    cooling_capacity_kw: float
    airflow_cfm: float | None
    power_consumption_kw: float | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CoolingUnitListResponse(BaseModel):
    cooling_units: list[CoolingUnitResponse]
    total: int
    page: int
    size: int
    pages: int


class ZoneCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Zone name",
        examples=["Zone-A"],
    )
    description: str | None = Field(
        None,
        description="Zone description",
    )
    target_temperature_min: float | None = Field(
        None,
        description="Minimum target temperature in C",
        examples=[18.0],
    )
    target_temperature_max: float | None = Field(
        None,
        description="Maximum target temperature in C",
        examples=[27.0],
    )
    target_humidity_min: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Minimum target humidity %",
        examples=[30.0],
    )
    target_humidity_max: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Maximum target humidity %",
        examples=[60.0],
    )
    status: CoolingStatus = Field(
        default=CoolingStatus.ACTIVE,
        description="Current status",
    )


class ZoneUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    target_temperature_min: float | None = None
    target_temperature_max: float | None = None
    target_humidity_min: float | None = Field(
        None,
        ge=0,
        le=100,
    )
    target_humidity_max: float | None = Field(
        None,
        ge=0,
        le=100,
    )
    status: CoolingStatus | None = None


class ZoneResponse(BaseModel):
    id: str
    company_id: str
    room_id: str
    name: str
    description: str | None
    target_temperature_min: float | None
    target_temperature_max: float | None
    target_humidity_min: float | None
    target_humidity_max: float | None
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ZoneListResponse(BaseModel):
    zones: list[ZoneResponse]
    total: int
    page: int
    size: int
    pages: int


class SensorCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Sensor name",
        examples=["Temp-Sensor-01"],
    )
    sensor_type: SensorType = Field(
        ...,
        description="Sensor type",
    )
    status: CoolingStatus = Field(
        default=CoolingStatus.ACTIVE,
        description="Current status",
    )
    location_description: str | None = Field(
        None,
        max_length=500,
        description="Physical location description",
        examples=["Rack Row A, Position U10"],
    )


class SensorUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    sensor_type: SensorType | None = None
    status: CoolingStatus | None = None
    location_description: str | None = Field(
        None,
        max_length=500,
    )
    last_value: float | None = None
    last_unit: str | None = Field(
        None,
        max_length=20,
    )
    last_reading_at: datetime | None = None


class SensorResponse(BaseModel):
    id: str
    company_id: str
    zone_id: str
    name: str
    sensor_type: str
    status: str
    location_description: str | None
    last_value: float | None
    last_unit: str | None
    last_reading_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SensorListResponse(BaseModel):
    sensors: list[SensorResponse]
    total: int
    page: int
    size: int
    pages: int


class RoomEnvironmentSummaryResponse(BaseModel):
    room_id: str
    room_name: str
    current_temperature: float | None
    current_humidity: float | None
    temperature_unit: str | None
    humidity_unit: str | None
    cooling_status: str
    cooling_capacity_kw: float
    active_cooling_units: int
    total_cooling_units: int
    active_warnings: list[dict]
    environmental_health: str
    zones: list[dict]


class DataCenterEnvironmentSummaryResponse(BaseModel):
    datacenter_id: str
    datacenter_name: str
    average_temperature: float | None
    average_humidity: float | None
    critical_rooms: list[dict]
    failed_cooling_units: list[dict]
    total_cooling_capacity_kw: float
    active_cooling_units: int
    total_cooling_units: int
    room_count: int
    room_summaries: list[dict]
