from datetime import datetime

from pydantic import BaseModel, Field


# --- Monitoring Target Schemas ---


class MonitoringTargetCreateRequest(BaseModel):
    enabled: bool = Field(
        default=True,
        description="Enable monitoring",
    )
    collector_type: str = Field(
        default="AGENT",
        description="Collector type",
    )
    endpoint: str | None = Field(
        None,
        max_length=500,
        description="Collector endpoint URL",
    )
    port: int | None = Field(
        None,
        ge=1,
        le=65535,
        description="Collector port",
    )
    interval_seconds: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="Collection interval in seconds",
    )


class MonitoringTargetUpdateRequest(BaseModel):
    enabled: bool | None = None
    collector_type: str | None = None
    endpoint: str | None = Field(
        None,
        max_length=500,
    )
    port: int | None = Field(
        None,
        ge=1,
        le=65535,
    )
    interval_seconds: int | None = Field(
        None,
        ge=10,
        le=3600,
    )
    status: str | None = None


class MonitoringTargetResponse(BaseModel):
    id: str
    company_id: str
    device_id: str
    enabled: bool
    collector_type: str
    endpoint: str | None
    port: int | None
    interval_seconds: int
    status: str
    last_check_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MonitoringTargetListResponse(BaseModel):
    targets: list[MonitoringTargetResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Metric Definition Schemas ---


class MetricDefinitionCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Metric display name",
        examples=["CPU Usage"],
    )
    metric_key: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique metric key",
        examples=["cpu_usage_percent"],
    )
    unit: str | None = Field(
        None,
        max_length=50,
        description="Measurement unit",
        examples=["%"],
    )
    description: str | None = Field(
        None,
        description="Metric description",
    )
    category: str = Field(
        default="OTHER",
        description="Metric category",
    )


class MetricDefinitionResponse(BaseModel):
    id: str
    name: str
    metric_key: str
    unit: str | None
    description: str | None
    category: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MetricDefinitionListResponse(BaseModel):
    definitions: list[MetricDefinitionResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Metric Data Schemas ---


class MetricDataCreateRequest(BaseModel):
    metric_definition_id: str = Field(
        ...,
        description="Metric definition UUID",
    )
    value: float = Field(
        ...,
        description="Metric value",
    )
    timestamp: datetime = Field(
        ...,
        description="Metric timestamp",
    )


class MetricDataResponse(BaseModel):
    id: str
    company_id: str
    device_id: str
    target_id: str
    metric_definition_id: str
    value: float
    timestamp: str
    created_at: str

    model_config = {"from_attributes": True}


class MetricDataListResponse(BaseModel):
    metrics: list[MetricDataResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Health Check Schemas ---


class HealthCheckResponse(BaseModel):
    id: str
    company_id: str
    device_id: str
    status: str
    response_time_ms: float | None
    checked_at: str
    created_at: str

    model_config = {"from_attributes": True}


class HealthCheckListResponse(BaseModel):
    health_checks: list[HealthCheckResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Dashboard Schemas ---


class DeviceLatestMetricsResponse(BaseModel):
    device_id: str
    metrics: list[dict]


class MonitoringSummaryResponse(BaseModel):
    datacenter_id: str
    datacenter_name: str
    total_devices: int
    online_devices: int
    offline_devices: int
    warning_devices: int
    unknown_devices: int
    average_cpu: float | None
    average_memory: float | None
    device_summaries: list[dict]


# --- Collector Status Schemas ---


class CollectorStatusResponse(BaseModel):
    collector_type: str
    available: bool
    version: str
    supported_metrics: list[str]
