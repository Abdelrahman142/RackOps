from datetime import datetime

from pydantic import BaseModel, Field


# --- Alert Rule Schemas ---


class AlertRuleCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Alert rule name",
        examples=["High CPU Usage"],
    )
    description: str | None = Field(
        None,
        description="Rule description",
    )
    metric_key: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Metric key to evaluate",
        examples=["cpu_usage_percent"],
    )
    condition: str = Field(
        ...,
        description="Comparison condition",
        examples=["GREATER_THAN"],
    )
    threshold_value: float = Field(
        ...,
        description="Threshold value",
        examples=[90.0],
    )
    severity: str = Field(
        default="WARNING",
        description="Alert severity",
    )
    enabled: bool = Field(
        default=True,
        description="Enable the rule",
    )
    evaluation_interval_seconds: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Evaluation interval in seconds",
    )


class AlertRuleUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    metric_key: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    condition: str | None = None
    threshold_value: float | None = None
    severity: str | None = None
    enabled: bool | None = None
    evaluation_interval_seconds: int | None = Field(
        None,
        ge=10,
        le=3600,
    )


class AlertRuleResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: str | None
    metric_key: str
    condition: str
    threshold_value: float
    severity: str
    enabled: bool
    evaluation_interval_seconds: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class AlertRuleListResponse(BaseModel):
    rules: list[AlertRuleResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Alert Schemas ---


class AlertResponse(BaseModel):
    id: str
    company_id: str
    device_id: str
    rule_id: str
    title: str
    description: str | None
    severity: str
    status: str
    triggered_at: str
    resolved_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    page: int
    size: int
    pages: int


class AlertSummaryResponse(BaseModel):
    total_alerts: int
    open_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int


# --- Incident Schemas ---


class IncidentCreateRequest(BaseModel):
    alert_id: str = Field(
        ...,
        description="Alert UUID that triggered this incident",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Incident title",
    )
    description: str | None = Field(
        None,
        description="Incident description",
    )
    priority: str = Field(
        default="MEDIUM",
        description="Incident priority",
    )
    assigned_user_id: str | None = Field(
        None,
        description="User UUID to assign",
    )


class IncidentUpdateRequest(BaseModel):
    title: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    assigned_user_id: str | None = None


class IncidentResolveRequest(BaseModel):
    resolution_notes: str | None = Field(
        None,
        description="Resolution notes",
    )


class IncidentResponse(BaseModel):
    id: str
    company_id: str
    alert_id: str
    title: str
    description: str | None
    priority: str
    status: str
    assigned_user_id: str | None
    created_at: str
    updated_at: str
    resolved_at: str | None

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    incidents: list[IncidentResponse]
    total: int
    page: int
    size: int
    pages: int


class IncidentSummaryResponse(BaseModel):
    open_incidents: int
    in_progress_incidents: int
    resolved_incidents: int
    closed_incidents: int
    average_resolution_time_minutes: float | None
    critical_incidents: int


# --- Maintenance Window Schemas ---


class MaintenanceWindowCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Window name",
    )
    description: str | None = Field(
        None,
        description="Window description",
    )
    start_time: datetime = Field(
        ...,
        description="Window start time",
    )
    end_time: datetime = Field(
        ...,
        description="Window end time",
    )


class MaintenanceWindowUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = None


class MaintenanceWindowResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: str | None
    start_time: str
    end_time: str
    created_by: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class MaintenanceWindowListResponse(BaseModel):
    windows: list[MaintenanceWindowResponse]
    total: int
    page: int
    size: int
    pages: int
