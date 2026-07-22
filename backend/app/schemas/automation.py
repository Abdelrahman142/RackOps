from datetime import datetime

from pydantic import BaseModel, Field


# --- Automation Job Schemas ---


class AutomationJobCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Job name",
        examples=["Execute uptime check"],
    )
    description: str | None = Field(
        None,
        description="Job description",
    )
    job_type: str = Field(
        ...,
        description="Job type: COMMAND, CONFIGURATION, BACKUP, DEPLOYMENT, MAINTENANCE",
        examples=["COMMAND"],
    )


class AutomationJobResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: str | None
    job_type: str
    status: str
    created_by: str
    started_at: str | None
    completed_at: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class AutomationJobListResponse(BaseModel):
    jobs: list[AutomationJobResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Device Connector Schemas ---


class DeviceConnectorCreateRequest(BaseModel):
    connector_type: str = Field(
        ...,
        description="Connector type: SSH, SNMP, API, ANSIBLE",
        examples=["SSH"],
    )
    hostname: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Device hostname or IP",
        examples=["192.168.1.100"],
    )
    port: int = Field(
        default=22,
        ge=1,
        le=65535,
        description="Connection port",
    )
    username: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Connection username",
    )
    password: str | None = Field(
        None,
        description="Connection password (will be encrypted)",
    )
    enabled: bool = Field(
        default=True,
        description="Enable the connector",
    )


class DeviceConnectorResponse(BaseModel):
    id: str
    device_id: str
    company_id: str
    connector_type: str
    hostname: str
    port: int
    username: str
    enabled: bool
    last_connection_test: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DeviceConnectorListResponse(BaseModel):
    connectors: list[DeviceConnectorResponse]
    total: int


class ConnectorTestResponse(BaseModel):
    connector_id: str
    success: bool
    message: str
    tested_at: str


# --- Automation Task Schemas ---


class AutomationTaskResponse(BaseModel):
    id: str
    job_id: str
    device_id: str
    company_id: str
    command: str
    parameters: str | None
    status: str
    output: str | None
    error_message: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class AutomationTaskListResponse(BaseModel):
    tasks: list[AutomationTaskResponse]
    total: int


# --- Configuration Backup Schemas ---


class ConfigurationBackupCreateRequest(BaseModel):
    device_id: str = Field(
        ...,
        description="Device UUID to backup",
    )
    backup_type: str = Field(
        ...,
        description="Backup type: FULL, CONFIG, DATABASE",
    )


class ConfigurationBackupResponse(BaseModel):
    id: str
    device_id: str
    company_id: str
    backup_type: str
    location: str
    size: float | None
    checksum: str | None
    status: str
    created_by: str
    created_at: str

    model_config = {"from_attributes": True}


class ConfigurationBackupListResponse(BaseModel):
    backups: list[ConfigurationBackupResponse]
    total: int


# --- Audit Log Schemas ---


class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    company_id: str
    action: str
    resource: str
    resource_id: str | None
    device_id: str | None
    details: str | None
    status: str
    ip_address: str | None
    created_at: str

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Automation Execute Request ---


class AutomationExecuteRequest(BaseModel):
    device_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of device UUIDs to execute against",
    )
    command: str = Field(
        ...,
        min_length=1,
        description="Command to execute",
    )
    parameters: str | None = Field(
        None,
        description="Optional command parameters",
    )
