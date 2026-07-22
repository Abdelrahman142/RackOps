import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.automation import (
    AutomationExecuteRequest,
    AutomationJobCreateRequest,
    AutomationJobListResponse,
    AutomationJobResponse,
    AutomationTaskListResponse,
    AutomationTaskResponse,
    AuditLogListResponse,
    AuditLogResponse,
    ConfigurationBackupCreateRequest,
    ConfigurationBackupListResponse,
    ConfigurationBackupResponse,
    ConnectorTestResponse,
    DeviceConnectorCreateRequest,
    DeviceConnectorListResponse,
    DeviceConnectorResponse,
)
from app.services.audit import AuditService
from app.services.automation import AutomationService
from app.services.backup import BackupService
from app.services.connector import ConnectorService

router = APIRouter(tags=["Automation & Infrastructure Operations"])

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


# --- Automation Jobs ---


@router.post(
    "/automation/jobs",
    response_model=AutomationJobResponse,
    status_code=201,
    summary="Create an automation job",
    description="Create a new automation job for device operations.",
    responses={
        201: {"description": "Job created"},
        422: {"description": "Validation error"},
    },
)
def create_automation_job(
    data: AutomationJobCreateRequest,
    current_user: User = Depends(RequireRole(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    service = AutomationService(db)
    audit = AuditService(db)
    job = service.create_job(
        company_id=current_user.company_id,
        name=data.name,
        job_type=data.job_type,
        created_by=current_user.id,
        description=data.description,
    )
    audit.log(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="CREATE",
        resource="AUTOMATION_JOB",
        resource_id=job["id"],
        details=f"Created job: {data.name} ({data.job_type})",
    )
    return job


@router.get(
    "/automation/jobs",
    response_model=AutomationJobListResponse,
    summary="List automation jobs",
    description="List all automation jobs with optional filters.",
)
def list_automation_jobs(
    current_user: User = Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
    job_type: str | None = Query(
        None, description="Filter by job type"
    ),
    status: str | None = Query(
        None, description="Filter by status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
):
    service = AutomationService(db)
    items, total = service.list_jobs(
        current_user.company_id, job_type, status, page, size
    )
    pages = (total + size - 1) // size if total > 0 else 1
    return AutomationJobListResponse(
        jobs=[AutomationJobResponse(**j) for j in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/automation/jobs/{job_id}",
    response_model=AutomationJobResponse,
    summary="Get an automation job",
    description="Get details of a specific automation job.",
    responses={
        200: {"description": "Job found"},
        404: {"description": "Job not found"},
    },
)
def get_automation_job(
    job_id: str,
    current_user: User = Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = AutomationService(db)
    return service.get_job(
        current_user.company_id, uuid.UUID(job_id)
    )


@router.post(
    "/automation/jobs/{job_id}/execute",
    response_model=AutomationJobResponse,
    summary="Execute an automation job",
    description="Execute a pending automation job.",
    responses={
        200: {"description": "Job executed"},
        404: {"description": "Job not found"},
        422: {"description": "Job not in PENDING status"},
    },
)
def execute_automation_job(
    job_id: str,
    current_user: User = Depends(RequireRole(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    service = AutomationService(db)
    audit = AuditService(db)
    job = service.execute_job(
        current_user.company_id, uuid.UUID(job_id)
    )
    audit.log(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="EXECUTE",
        resource="AUTOMATION_JOB",
        resource_id=job["id"],
        details=f"Executed job: {job['name']}",
    )
    return job


@router.post(
    "/automation/jobs/{job_id}/cancel",
    response_model=AutomationJobResponse,
    summary="Cancel an automation job",
    description="Cancel a pending or running automation job.",
    responses={
        200: {"description": "Job cancelled"},
        404: {"description": "Job not found"},
        422: {"description": "Job cannot be cancelled"},
    },
)
def cancel_automation_job(
    job_id: str,
    current_user: User = Depends(RequireRole(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    service = AutomationService(db)
    audit = AuditService(db)
    job = service.cancel_job(
        current_user.company_id, uuid.UUID(job_id)
    )
    audit.log(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="CANCEL",
        resource="AUTOMATION_JOB",
        resource_id=job["id"],
        details=f"Cancelled job: {job['name']}",
    )
    return job


@router.get(
    "/automation/jobs/{job_id}/tasks",
    response_model=AutomationTaskListResponse,
    summary="List tasks for an automation job",
    description="List all tasks associated with an automation job.",
)
def list_automation_tasks(
    job_id: str,
    current_user: User = Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = AutomationService(db)
    tasks = service.list_tasks(
        current_user.company_id, uuid.UUID(job_id)
    )
    return AutomationTaskListResponse(
        tasks=[AutomationTaskResponse(**t) for t in tasks],
        total=len(tasks),
    )


@router.post(
    "/automation/execute",
    response_model=AutomationJobResponse,
    status_code=201,
    summary="Execute command on devices",
    description="Create and execute a command job on multiple devices.",
)
def execute_on_devices(
    data: AutomationExecuteRequest,
    current_user: User = Depends(RequireRole(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    service = AutomationService(db)
    audit = AuditService(db)

    job = service.create_job(
        company_id=current_user.company_id,
        name=f"Execute: {data.command[:50]}",
        job_type="COMMAND",
        created_by=current_user.id,
        description=f"Command: {data.command}",
    )

    for device_id_str in data.device_ids:
        service.create_task_for_job(
            company_id=current_user.company_id,
            job_id=uuid.UUID(job["id"]),
            device_id=uuid.UUID(device_id_str),
            command=data.command,
            parameters=data.parameters,
        )

    job = service.execute_job(
        current_user.company_id, uuid.UUID(job["id"])
    )

    audit.log(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="EXECUTE_COMMAND",
        resource="AUTOMATION_JOB",
        resource_id=job["id"],
        details=f"Executed '{data.command}' on {len(data.device_ids)} devices",
    )
    return job


# --- Device Connectors ---


@router.post(
    "/devices/{device_id}/connectors",
    response_model=DeviceConnectorResponse,
    status_code=201,
    summary="Create a device connector",
    description="Create a new connector for a device.",
    responses={
        201: {"description": "Connector created"},
        422: {"description": "Validation error"},
    },
)
def create_device_connector(
    device_id: str,
    data: DeviceConnectorCreateRequest,
    current_user: User = Depends(RequireRole(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    service = ConnectorService(db)
    audit = AuditService(db)
    connector = service.create_connector(
        device_id=uuid.UUID(device_id),
        company_id=current_user.company_id,
        connector_type=data.connector_type,
        hostname=data.hostname,
        port=data.port,
        username=data.username,
        password=data.password,
        enabled=data.enabled,
    )
    audit.log(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="CREATE",
        resource="DEVICE_CONNECTOR",
        resource_id=connector["id"],
        device_id=uuid.UUID(device_id),
        details=f"Created {data.connector_type} connector to {data.hostname}",
    )
    return connector


@router.get(
    "/devices/{device_id}/connectors",
    response_model=DeviceConnectorListResponse,
    summary="List device connectors",
    description="List all connectors for a device.",
)
def list_device_connectors(
    device_id: str,
    current_user: User = Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = ConnectorService(db)
    connectors = service.list_connectors_for_device(
        current_user.company_id, uuid.UUID(device_id)
    )
    return DeviceConnectorListResponse(
        connectors=[
            DeviceConnectorResponse(**c)
            for c in connectors
        ],
        total=len(connectors),
    )


@router.post(
    "/connectors/{connector_id}/test",
    response_model=ConnectorTestResponse,
    summary="Test a device connector",
    description="Test connectivity to a device via its connector.",
    responses={
        200: {"description": "Test completed"},
        404: {"description": "Connector not found"},
    },
)
def test_connector(
    connector_id: str,
    current_user: User = Depends(RequireRole(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    service = ConnectorService(db)
    audit = AuditService(db)
    result = service.test_connector(
        current_user.company_id, uuid.UUID(connector_id)
    )
    audit.log(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="TEST_CONNECTOR",
        resource="DEVICE_CONNECTOR",
        resource_id=connector_id,
        details=f"Test result: {'success' if result['success'] else 'failed'}",
        status="SUCCESS" if result["success"] else "FAILED",
    )
    return result


# --- Configuration Backups ---


@router.post(
    "/devices/{device_id}/backups",
    response_model=ConfigurationBackupResponse,
    status_code=201,
    summary="Create a configuration backup",
    description="Create a new configuration backup for a device.",
    responses={
        201: {"description": "Backup created"},
        422: {"description": "Validation error"},
    },
)
def create_backup(
    device_id: str,
    data: ConfigurationBackupCreateRequest,
    current_user: User = Depends(RequireRole(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    service = BackupService(db)
    audit = AuditService(db)
    backup = service.create_backup(
        device_id=uuid.UUID(device_id),
        company_id=current_user.company_id,
        backup_type=data.backup_type,
        created_by=current_user.id,
    )
    audit.log(
        user_id=current_user.id,
        company_id=current_user.company_id,
        action="CREATE_BACKUP",
        resource="CONFIGURATION_BACKUP",
        resource_id=backup["id"],
        device_id=uuid.UUID(device_id),
        details=f"Created {data.backup_type} backup",
    )
    return backup


@router.get(
    "/devices/{device_id}/backups",
    response_model=ConfigurationBackupListResponse,
    summary="List device backups",
    description="List all configuration backups for a device.",
)
def list_backups(
    device_id: str,
    current_user: User = Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = BackupService(db)
    backups = service.list_backups_for_device(
        current_user.company_id, uuid.UUID(device_id)
    )
    return ConfigurationBackupListResponse(
        backups=[
            ConfigurationBackupResponse(**b)
            for b in backups
        ],
        total=len(backups),
    )


# --- Audit Logs ---


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    description="List audit logs with optional filters.",
)
def list_audit_logs(
    current_user: User = Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
    action: str | None = Query(
        None, description="Filter by action"
    ),
    resource: str | None = Query(
        None, description="Filter by resource"
    ),
    device_id: str | None = Query(
        None, description="Filter by device ID"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
):
    service = AuditService(db)
    dev_uuid = uuid.UUID(device_id) if device_id else None
    items, total = service.list_logs(
        current_user.company_id,
        action=action,
        resource=resource,
        device_id=dev_uuid,
        page=page,
        size=size,
    )
    pages = (total + size - 1) // size if total > 0 else 1
    return AuditLogListResponse(
        logs=[AuditLogResponse(**l) for l in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )
