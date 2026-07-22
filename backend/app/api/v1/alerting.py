import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.alerting import (
    AlertListResponse,
    AlertResponse,
    AlertRuleCreateRequest,
    AlertRuleListResponse,
    AlertRuleResponse,
    AlertRuleUpdateRequest,
    AlertSummaryResponse,
    IncidentCreateRequest,
    IncidentListResponse,
    IncidentResponse,
    IncidentResolveRequest,
    IncidentSummaryResponse,
    IncidentUpdateRequest,
    MaintenanceWindowCreateRequest,
    MaintenanceWindowListResponse,
    MaintenanceWindowResponse,
    MaintenanceWindowUpdateRequest,
)
from app.services.alerting import AlertingService

router = APIRouter(
    tags=["Alerting & Incident Management"],
)

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


class AlertCreateRequest(BaseModel):
    device_id: str = Field(
        ...,
        description="Device UUID",
    )
    rule_id: str = Field(
        ...,
        description="Alert rule UUID",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Alert title",
    )
    severity: str = Field(
        ...,
        description="Alert severity",
    )
    description: str | None = Field(
        None,
        description="Alert description",
    )


# --- Alert Rule Endpoints ---


@router.post(
    "/alert-rules",
    response_model=AlertRuleResponse,
    status_code=201,
    summary="Create an alert rule",
    description=(
        "Create a new alert rule for monitoring "
        "metrics against thresholds."
    ),
    responses={
        201: {"description": "Rule created"},
        422: {"description": "Validation error"},
    },
)
def create_alert_rule(
    data: AlertRuleCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.create_rule(
        company_id=current_user.company_id,
        name=data.name,
        description=data.description,
        metric_key=data.metric_key,
        condition=data.condition,
        threshold_value=data.threshold_value,
        severity=data.severity,
        enabled=data.enabled,
        evaluation_interval_seconds=(
            data.evaluation_interval_seconds
        ),
    )


@router.get(
    "/alert-rules",
    response_model=AlertRuleListResponse,
    summary="List alert rules",
    description=(
        "List all alert rules with optional filters."
    ),
)
def list_alert_rules(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    severity: str | None = Query(
        None,
        description="Filter by severity",
    ),
    enabled: bool | None = Query(
        None,
        description="Filter by enabled status",
    ),
    metric_key: str | None = Query(
        None,
        description="Filter by metric key",
    ),
    page: int = Query(
        1, ge=1, description="Page number"
    ),
    size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
):
    service = AlertingService(db)
    return service.list_rules(
        company_id=current_user.company_id,
        severity=severity,
        enabled=enabled,
        metric_key=metric_key,
        page=page,
        size=size,
    )


@router.get(
    "/alert-rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Get an alert rule",
    description="Get details of a specific alert rule.",
    responses={
        404: {"description": "Rule not found"},
    },
)
def get_alert_rule(
    rule_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.get_rule(
        company_id=current_user.company_id,
        rule_id=uuid.UUID(rule_id),
    )


@router.patch(
    "/alert-rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Update an alert rule",
    description="Update an existing alert rule.",
    responses={
        200: {"description": "Rule updated"},
        404: {"description": "Rule not found"},
    },
)
def update_alert_rule(
    rule_id: str,
    data: AlertRuleUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.update_rule(
        company_id=current_user.company_id,
        rule_id=uuid.UUID(rule_id),
        name=data.name,
        description=data.description,
        metric_key=data.metric_key,
        condition=data.condition,
        threshold_value=data.threshold_value,
        severity=data.severity,
        enabled=data.enabled,
        evaluation_interval_seconds=(
            data.evaluation_interval_seconds
        ),
    )


@router.delete(
    "/alert-rules/{rule_id}",
    summary="Delete an alert rule",
    description="Soft delete an alert rule.",
    responses={
        200: {"description": "Rule deleted"},
        404: {"description": "Rule not found"},
    },
)
def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.delete_rule(
        company_id=current_user.company_id,
        rule_id=uuid.UUID(rule_id),
    )


# --- Alert Endpoints ---


@router.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=201,
    summary="Create an alert",
    description=(
        "Create a new alert for a device."
    ),
    responses={
        201: {"description": "Alert created"},
        404: {"description": "Rule or device not found"},
    },
)
def create_alert(
    data: AlertCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    from app.repositories.alert import (
        AlertRepository,
    )
    from app.repositories.alert_rule import (
        AlertRuleRepository,
    )

    rule_repo = AlertRuleRepository(db)
    rule = rule_repo.get_by_id(
        current_user.company_id,
        uuid.UUID(data.rule_id),
    )
    if not rule:
        from app.utils.exceptions import (
            NotFoundException,
        )

        raise NotFoundException(
            detail="Alert rule not found"
        )

    alert_repo = AlertRepository(db)
    alert = alert_repo.create(
        company_id=current_user.company_id,
        device_id=uuid.UUID(data.device_id),
        rule_id=uuid.UUID(data.rule_id),
        title=data.title,
        severity=data.severity,
        description=data.description,
    )
    db.commit()
    db.refresh(alert)
    return service._serialize_alert(alert)


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="List alerts",
    description=(
        "List all alerts with optional filters."
    ),
)
def list_alerts(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    severity: str | None = Query(
        None,
        description="Filter by severity",
    ),
    device_id: str | None = Query(
        None,
        description="Filter by device UUID",
    ),
    rule_id: str | None = Query(
        None,
        description="Filter by rule UUID",
    ),
    page: int = Query(
        1, ge=1, description="Page number"
    ),
    size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
):
    service = AlertingService(db)
    parsed_device = (
        uuid.UUID(device_id) if device_id else None
    )
    parsed_rule = (
        uuid.UUID(rule_id) if rule_id else None
    )
    return service.list_alerts(
        company_id=current_user.company_id,
        status=status,
        severity=severity,
        device_id=parsed_device,
        rule_id=parsed_rule,
        page=page,
        size=size,
    )


@router.get(
    "/alerts/summary",
    response_model=AlertSummaryResponse,
    summary="Get alert summary",
    description=(
        "Get a summary of alerts including counts "
        "by status and severity."
    ),
)
def get_alert_summary(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.get_alert_summary(
        company_id=current_user.company_id,
    )


@router.get(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    summary="Get an alert",
    description="Get details of a specific alert.",
    responses={
        404: {"description": "Alert not found"},
    },
)
def get_alert(
    alert_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.get_alert(
        company_id=current_user.company_id,
        alert_id=uuid.UUID(alert_id),
    )


@router.patch(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge an alert",
    description="Acknowledge an open alert.",
    responses={
        200: {"description": "Alert acknowledged"},
        404: {"description": "Alert not found"},
    },
)
def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.acknowledge_alert(
        company_id=current_user.company_id,
        alert_id=uuid.UUID(alert_id),
    )


@router.patch(
    "/alerts/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Resolve an alert",
    description="Resolve an open or acknowledged alert.",
    responses={
        200: {"description": "Alert resolved"},
        404: {"description": "Alert not found"},
    },
)
def resolve_alert(
    alert_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.resolve_alert(
        company_id=current_user.company_id,
        alert_id=uuid.UUID(alert_id),
    )


# --- Incident Endpoints ---


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=201,
    summary="Create an incident",
    description=(
        "Create a new incident from an alert."
    ),
    responses={
        201: {"description": "Incident created"},
        404: {"description": "Alert not found"},
        409: {
            "description": "Incident already exists"
        },
    },
)
def create_incident(
    data: IncidentCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    parsed_user = (
        uuid.UUID(data.assigned_user_id)
        if data.assigned_user_id
        else None
    )
    return service.create_incident(
        company_id=current_user.company_id,
        alert_id=uuid.UUID(data.alert_id),
        title=data.title,
        description=data.description,
        priority=data.priority,
        assigned_user_id=parsed_user,
    )


@router.get(
    "/incidents",
    response_model=IncidentListResponse,
    summary="List incidents",
    description=(
        "List all incidents with optional filters."
    ),
)
def list_incidents(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    priority: str | None = Query(
        None,
        description="Filter by priority",
    ),
    assigned_user_id: str | None = Query(
        None,
        description="Filter by assigned user UUID",
    ),
    page: int = Query(
        1, ge=1, description="Page number"
    ),
    size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
):
    service = AlertingService(db)
    parsed_user = (
        uuid.UUID(assigned_user_id)
        if assigned_user_id
        else None
    )
    return service.list_incidents(
        company_id=current_user.company_id,
        status=status,
        priority=priority,
        assigned_user_id=parsed_user,
        page=page,
        size=size,
    )


@router.get(
    "/incidents/summary",
    response_model=IncidentSummaryResponse,
    summary="Get incident summary",
    description=(
        "Get a summary of incidents including "
        "resolution metrics."
    ),
)
def get_incident_summary(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.get_incident_summary(
        company_id=current_user.company_id,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
    summary="Get an incident",
    description="Get details of a specific incident.",
    responses={
        404: {"description": "Incident not found"},
    },
)
def get_incident(
    incident_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.get_incident(
        company_id=current_user.company_id,
        incident_id=uuid.UUID(incident_id),
    )


@router.patch(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
    summary="Update an incident",
    description=(
        "Update incident details, status, or assignment."
    ),
    responses={
        200: {"description": "Incident updated"},
        404: {"description": "Incident not found"},
    },
)
def update_incident(
    incident_id: str,
    data: IncidentUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.update_incident(
        company_id=current_user.company_id,
        incident_id=uuid.UUID(incident_id),
        title=data.title,
        description=data.description,
        priority=data.priority,
        status=data.status,
        assigned_user_id=data.assigned_user_id,
    )


@router.patch(
    "/incidents/{incident_id}/resolve",
    response_model=IncidentResponse,
    summary="Resolve an incident",
    description=(
        "Mark an incident as resolved."
    ),
    responses={
        200: {"description": "Incident resolved"},
        404: {"description": "Incident not found"},
    },
)
def resolve_incident(
    incident_id: str,
    data: IncidentResolveRequest | None = None,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.resolve_incident(
        company_id=current_user.company_id,
        incident_id=uuid.UUID(incident_id),
    )


# --- Maintenance Window Endpoints ---


@router.post(
    "/maintenance-windows",
    response_model=MaintenanceWindowResponse,
    status_code=201,
    summary="Create a maintenance window",
    description=(
        "Schedule a new maintenance window. "
        "Alerts are suppressed during active windows."
    ),
    responses={
        201: {"description": "Window created"},
        422: {
            "description": "Validation error"
        },
    },
)
def create_maintenance_window(
    data: MaintenanceWindowCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.create_window(
        company_id=current_user.company_id,
        name=data.name,
        description=data.description,
        start_time=data.start_time,
        end_time=data.end_time,
        created_by=current_user.id,
    )


@router.get(
    "/maintenance-windows",
    response_model=MaintenanceWindowListResponse,
    summary="List maintenance windows",
    description=(
        "List all maintenance windows."
    ),
)
def list_maintenance_windows(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    page: int = Query(
        1, ge=1, description="Page number"
    ),
    size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
):
    service = AlertingService(db)
    return service.list_windows(
        company_id=current_user.company_id,
        status=status,
        page=page,
        size=size,
    )


@router.get(
    "/maintenance-windows/{window_id}",
    response_model=MaintenanceWindowResponse,
    summary="Get a maintenance window",
    description="Get details of a maintenance window.",
    responses={
        404: {"description": "Window not found"},
    },
)
def get_maintenance_window(
    window_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.get_window(
        company_id=current_user.company_id,
        window_id=uuid.UUID(window_id),
    )


@router.patch(
    "/maintenance-windows/{window_id}",
    response_model=MaintenanceWindowResponse,
    summary="Update a maintenance window",
    description="Update a maintenance window.",
    responses={
        200: {"description": "Window updated"},
        404: {"description": "Window not found"},
    },
)
def update_maintenance_window(
    window_id: str,
    data: MaintenanceWindowUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.update_window(
        company_id=current_user.company_id,
        window_id=uuid.UUID(window_id),
        name=data.name,
        description=data.description,
        start_time=data.start_time,
        end_time=data.end_time,
        status=data.status,
    )


@router.delete(
    "/maintenance-windows/{window_id}",
    summary="Delete a maintenance window",
    description="Delete a maintenance window.",
    responses={
        200: {"description": "Window deleted"},
        404: {"description": "Window not found"},
    },
)
def delete_maintenance_window(
    window_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = AlertingService(db)
    return service.delete_window(
        company_id=current_user.company_id,
        window_id=uuid.UUID(window_id),
    )
