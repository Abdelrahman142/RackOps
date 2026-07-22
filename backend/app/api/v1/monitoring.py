import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.monitoring import (
    CollectorStatusResponse,
    DeviceLatestMetricsResponse,
    HealthCheckListResponse,
    HealthCheckResponse,
    MetricDataCreateRequest,
    MetricDataListResponse,
    MetricDataResponse,
    MetricDefinitionCreateRequest,
    MetricDefinitionListResponse,
    MetricDefinitionResponse,
    MonitoringSummaryResponse,
    MonitoringTargetCreateRequest,
    MonitoringTargetListResponse,
    MonitoringTargetResponse,
    MonitoringTargetUpdateRequest,
)
from app.services.metric_scheduler import (
    MetricCollectionScheduler,
)
from app.services.monitoring import MonitoringService

router = APIRouter(
    tags=["Monitoring & Metrics"],
)

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


# --- Monitoring Target Endpoints ---


@router.post(
    "/devices/{device_id}/monitoring",
    response_model=MonitoringTargetResponse,
    status_code=201,
    summary="Create a monitoring target for a device",
    description=(
        "Register a device for monitoring with a "
        "specific collector type."
    ),
    responses={
        201: {"description": "Target created"},
        404: {"description": "Device not found"},
        409: {
            "description": "Target already exists"
        },
        422: {"description": "Validation error"},
    },
)
def create_monitoring_target(
    device_id: str,
    data: MonitoringTargetCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.create_target(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
        enabled=data.enabled,
        collector_type=data.collector_type,
        endpoint=data.endpoint,
        port=data.port,
        interval_seconds=data.interval_seconds,
    )


@router.get(
    "/devices/{device_id}/monitoring",
    response_model=MonitoringTargetResponse,
    summary="Get monitoring target for a device",
    description=(
        "Get the monitoring target configuration "
        "for a specific device."
    ),
    responses={
        404: {"description": "Target not found"},
    },
)
def get_device_monitoring(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    target_repo = service.target_repo
    target = target_repo.get_by_device(
        current_user.company_id,
        uuid.UUID(device_id),
    )

    if not target:
        from app.utils.exceptions import (
            NotFoundException,
        )

        raise NotFoundException(
            detail="Monitoring target not found"
        )

    return service._serialize_target(target)


@router.get(
    "/monitoring",
    response_model=MonitoringTargetListResponse,
    summary="List all monitoring targets",
    description=(
        "List all monitoring targets with "
        "filtering, sorting, and pagination."
    ),
)
def list_monitoring_targets(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    enabled: bool | None = Query(
        None,
        description="Filter by enabled status",
    ),
    collector_type: str | None = Query(
        None,
        description="Filter by collector type",
    ),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    sort_by: str = Query(
        "created_at",
        description="Sort field",
    ),
    sort_order: str = Query(
        "desc",
        description="Sort order: asc or desc",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
):
    service = MonitoringService(db)
    return service.list_targets(
        company_id=current_user.company_id,
        enabled=enabled,
        collector_type=collector_type,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/monitoring/{target_id}",
    response_model=MonitoringTargetResponse,
    summary="Get a monitoring target",
    description="Get details of a specific monitoring target.",
    responses={
        404: {"description": "Target not found"},
    },
)
def get_monitoring_target(
    target_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.get_target(
        company_id=current_user.company_id,
        target_id=uuid.UUID(target_id),
    )


@router.patch(
    "/monitoring/{target_id}",
    response_model=MonitoringTargetResponse,
    summary="Update a monitoring target",
    description="Update a monitoring target configuration.",
    responses={
        200: {"description": "Target updated"},
        404: {"description": "Target not found"},
    },
)
def update_monitoring_target(
    target_id: str,
    data: MonitoringTargetUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.update_target(
        company_id=current_user.company_id,
        target_id=uuid.UUID(target_id),
        enabled=data.enabled,
        collector_type=data.collector_type,
        endpoint=data.endpoint,
        port=data.port,
        interval_seconds=data.interval_seconds,
        status=data.status,
    )


@router.delete(
    "/monitoring/{target_id}",
    summary="Delete a monitoring target",
    description="Soft delete a monitoring target.",
    responses={
        200: {"description": "Target deleted"},
        404: {"description": "Target not found"},
    },
)
def delete_monitoring_target(
    target_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.delete_target(
        company_id=current_user.company_id,
        target_id=uuid.UUID(target_id),
    )


# --- Metric Definition Endpoints ---


@router.post(
    "/metric-definitions",
    response_model=MetricDefinitionResponse,
    status_code=201,
    summary="Create a metric definition",
    description=(
        "Create a new metric definition "
        "(CPU, Memory, Disk, etc.)."
    ),
    responses={
        201: {"description": "Definition created"},
        409: {"description": "Duplicate metric key"},
    },
)
def create_metric_definition(
    data: MetricDefinitionCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.create_definition(
        name=data.name,
        metric_key=data.metric_key,
        unit=data.unit,
        description=data.description,
        category=data.category,
    )


@router.get(
    "/metric-definitions",
    response_model=MetricDefinitionListResponse,
    summary="List metric definitions",
    description=(
        "List all metric definitions with "
        "optional category filter."
    ),
)
def list_metric_definitions(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    category: str | None = Query(
        None,
        description="Filter by category",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
):
    service = MonitoringService(db)
    return service.list_definitions(
        category=category,
        page=page,
        size=size,
    )


@router.get(
    "/metric-definitions/{definition_id}",
    response_model=MetricDefinitionResponse,
    summary="Get a metric definition",
    description="Get details of a specific metric definition.",
    responses={
        404: {"description": "Definition not found"},
    },
)
def get_metric_definition(
    definition_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.get_definition(
        uuid.UUID(definition_id)
    )


# --- Metric Data Endpoints ---


@router.post(
    "/devices/{device_id}/metrics",
    response_model=MetricDataResponse,
    status_code=201,
    summary="Store a metric data point",
    description=(
        "Store a metric data point for a device."
    ),
    responses={
        201: {"description": "Metric stored"},
        404: {"description": "Target or definition not found"},
    },
)
def store_metric(
    device_id: str,
    data: MetricDataCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    target_repo = service.target_repo
    target = target_repo.get_by_device(
        current_user.company_id,
        uuid.UUID(device_id),
    )

    if not target:
        from app.utils.exceptions import (
            NotFoundException,
        )

        raise NotFoundException(
            detail=(
                "No monitoring target for this device"
            )
        )

    return service.store_metric(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
        target_id=target.id,
        metric_definition_id=uuid.UUID(
            data.metric_definition_id
        ),
        value=data.value,
        timestamp=data.timestamp,
    )


@router.get(
    "/devices/{device_id}/metrics",
    response_model=MetricDataListResponse,
    summary="List metrics for a device",
    description=(
        "List all metrics for a device "
        "with optional filters."
    ),
)
def list_device_metrics(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    metric_definition_id: str | None = Query(
        None,
        description="Filter by metric definition",
    ),
    start_time: datetime | None = Query(
        None,
        description="Start time filter",
    ),
    end_time: datetime | None = Query(
        None,
        description="End time filter",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    size: int = Query(
        100,
        ge=1,
        le=1000,
        description="Items per page",
    ),
):
    service = MonitoringService(db)
    return service.list_device_metrics(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
        metric_definition_id=(
            uuid.UUID(metric_definition_id)
            if metric_definition_id
            else None
        ),
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
    )


@router.get(
    "/devices/{device_id}/metrics/latest",
    response_model=DeviceLatestMetricsResponse,
    summary="Get latest metrics for a device",
    description=(
        "Get the most recent metric value for "
        "each metric type on a device."
    ),
)
def get_latest_metrics(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.get_latest_metrics(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
    )


# --- Health Endpoints ---


@router.get(
    "/devices/{device_id}/health",
    summary="Get latest health check for a device",
    description=(
        "Get the most recent health check status "
        "for a device. Returns UNKNOWN status if "
        "no health data exists."
    ),
)
def get_device_health(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.get_device_health(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
    )


@router.get(
    "/devices/{device_id}/health/history",
    response_model=HealthCheckListResponse,
    summary="List health check history for a device",
    description=(
        "List health check history for a device."
    ),
)
def list_health_checks(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    start_time: datetime | None = Query(
        None,
        description="Start time filter",
    ),
    end_time: datetime | None = Query(
        None,
        description="End time filter",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    size: int = Query(
        100,
        ge=1,
        le=1000,
        description="Items per page",
    ),
):
    service = MonitoringService(db)
    return service.list_device_health_checks(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
        status=status,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
    )


# --- Action Endpoints ---


@router.post(
    "/monitoring/{target_id}/check",
    response_model=HealthCheckResponse,
    summary="Run a health check on a target",
    description=(
        "Trigger an immediate health check "
        "for a monitoring target."
    ),
    responses={
        200: {"description": "Health check result"},
        404: {"description": "Target not found"},
    },
)
def run_health_check(
    target_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.run_health_check(
        company_id=current_user.company_id,
        target_id=uuid.UUID(target_id),
    )


@router.post(
    "/monitoring/{target_id}/collect",
    response_model=list[MetricDataResponse],
    summary="Trigger metric collection for a target",
    description=(
        "Trigger an immediate metric collection "
        "for a monitoring target."
    ),
    responses={
        200: {"description": "Collected metrics"},
        404: {"description": "Target not found"},
        422: {
            "description": "Target is disabled"
        },
    },
)
def run_metric_collection(
    target_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.run_metric_collection(
        company_id=current_user.company_id,
        target_id=uuid.UUID(target_id),
    )


# --- Dashboard Endpoints ---


@router.get(
    "/datacenters/{datacenter_id}/monitoring-summary",
    response_model=MonitoringSummaryResponse,
    summary="Get monitoring summary for a datacenter",
    description=(
        "Get monitoring dashboard data for a data center "
        "including device health, CPU, and memory averages."
    ),
    responses={
        404: {"description": "Data center not found"},
    },
)
def get_monitoring_summary(
    datacenter_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.get_datacenter_monitoring_summary(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
    )


# --- Collector Info Endpoints ---


@router.get(
    "/collectors",
    response_model=list[CollectorStatusResponse],
    summary="List available collectors",
    description=(
        "List all available metric collectors "
        "and their supported metrics."
    ),
)
def list_collectors(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = MonitoringService(db)
    return service.get_collector_info()
