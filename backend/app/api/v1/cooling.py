import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.cooling import (
    CoolingStatus,
    CoolingUnitCreateRequest,
    CoolingUnitListResponse,
    CoolingUnitResponse,
    CoolingUnitType,
    CoolingUnitUpdateRequest,
    DataCenterEnvironmentSummaryResponse,
    RoomEnvironmentSummaryResponse,
    SensorCreateRequest,
    SensorListResponse,
    SensorResponse,
    SensorType,
    SensorUpdateRequest,
    ZoneCreateRequest,
    ZoneListResponse,
    ZoneResponse,
    ZoneUpdateRequest,
)
from app.services.cooling import CoolingService

router = APIRouter(
    tags=["Cooling & Environmental Monitoring"],
)

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


# --- Cooling Unit Endpoints ---


@router.post(
    "/rooms/{room_id}/cooling-units",
    response_model=CoolingUnitResponse,
    status_code=201,
    summary="Create a cooling unit in a room",
    description=(
        "Create a new cooling unit (CRAC, CRAH, "
        "chiller, fan wall, etc.) in a room."
    ),
    responses={
        201: {"description": "Cooling unit created"},
        404: {"description": "Room not found"},
        409: {
            "description": (
                "Duplicate name or serial number"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_cooling_unit(
    room_id: str,
    data: CoolingUnitCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.create_unit(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        name=data.name,
        cooling_capacity_kw=data.cooling_capacity_kw,
        manufacturer=data.manufacturer,
        model=data.model,
        serial_number=data.serial_number,
        type=data.type.value,
        status=data.status.value,
        airflow_cfm=data.airflow_cfm,
        power_consumption_kw=data.power_consumption_kw,
    )


@router.get(
    "/rooms/{room_id}/cooling-units",
    response_model=CoolingUnitListResponse,
    summary="List cooling units in a room",
    description=(
        "List all cooling units in a room "
        "with filtering, sorting, and pagination."
    ),
)
def list_cooling_units(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: CoolingStatus | None = Query(
        None,
        description="Filter by status",
    ),
    type: CoolingUnitType | None = Query(
        None,
        description="Filter by type",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
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
    service = CoolingService(db)
    return service.list_units(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        status=status.value if status else None,
        type=type.value if type else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/cooling-units/{unit_id}",
    response_model=CoolingUnitResponse,
    summary="Get a cooling unit",
    description="Get details of a specific cooling unit.",
    responses={
        404: {"description": "Cooling unit not found"},
    },
)
def get_cooling_unit(
    unit_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.get_unit(
        company_id=current_user.company_id,
        unit_id=uuid.UUID(unit_id),
    )


@router.patch(
    "/cooling-units/{unit_id}",
    response_model=CoolingUnitResponse,
    summary="Update a cooling unit",
    description="Update a cooling unit.",
    responses={
        200: {"description": "Cooling unit updated"},
        404: {"description": "Cooling unit not found"},
        409: {
            "description": (
                "Duplicate name or serial number"
            )
        },
    },
)
def update_cooling_unit(
    unit_id: str,
    data: CoolingUnitUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.update_unit(
        company_id=current_user.company_id,
        unit_id=uuid.UUID(unit_id),
        name=data.name,
        manufacturer=data.manufacturer,
        model=data.model,
        serial_number=data.serial_number,
        type=data.type.value if data.type else None,
        status=data.status.value if data.status else None,
        cooling_capacity_kw=data.cooling_capacity_kw,
        airflow_cfm=data.airflow_cfm,
        power_consumption_kw=data.power_consumption_kw,
    )


@router.delete(
    "/cooling-units/{unit_id}",
    summary="Delete a cooling unit",
    description="Soft delete a cooling unit.",
    responses={
        200: {"description": "Cooling unit deleted"},
        404: {"description": "Cooling unit not found"},
    },
)
def delete_cooling_unit(
    unit_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.delete_unit(
        company_id=current_user.company_id,
        unit_id=uuid.UUID(unit_id),
    )


# --- Zone Endpoints ---


@router.post(
    "/rooms/{room_id}/zones",
    response_model=ZoneResponse,
    status_code=201,
    summary="Create an environmental zone",
    description=(
        "Create an environmental monitoring zone in a room."
    ),
    responses={
        201: {"description": "Zone created"},
        404: {"description": "Room not found"},
        409: {"description": "Duplicate name"},
        422: {"description": "Validation error"},
    },
)
def create_zone(
    room_id: str,
    data: ZoneCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.create_zone(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        name=data.name,
        description=data.description,
        target_temperature_min=(
            data.target_temperature_min
        ),
        target_temperature_max=(
            data.target_temperature_max
        ),
        target_humidity_min=data.target_humidity_min,
        target_humidity_max=data.target_humidity_max,
        status=data.status.value,
    )


@router.get(
    "/rooms/{room_id}/zones",
    response_model=ZoneListResponse,
    summary="List environmental zones in a room",
    description=(
        "List all environmental zones in a room."
    ),
)
def list_zones(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: CoolingStatus | None = Query(
        None,
        description="Filter by status",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
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
    service = CoolingService(db)
    return service.list_zones(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        status=status.value if status else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Get an environmental zone",
    description="Get details of a specific zone.",
    responses={
        404: {"description": "Zone not found"},
    },
)
def get_zone(
    zone_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.get_zone(
        company_id=current_user.company_id,
        zone_id=uuid.UUID(zone_id),
    )


@router.patch(
    "/zones/{zone_id}",
    response_model=ZoneResponse,
    summary="Update an environmental zone",
    description="Update an environmental zone.",
    responses={
        200: {"description": "Zone updated"},
        404: {"description": "Zone not found"},
        409: {"description": "Duplicate name"},
    },
)
def update_zone(
    zone_id: str,
    data: ZoneUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.update_zone(
        company_id=current_user.company_id,
        zone_id=uuid.UUID(zone_id),
        name=data.name,
        description=data.description,
        target_temperature_min=(
            data.target_temperature_min
        ),
        target_temperature_max=(
            data.target_temperature_max
        ),
        target_humidity_min=data.target_humidity_min,
        target_humidity_max=data.target_humidity_max,
        status=data.status.value if data.status else None,
    )


# --- Sensor Endpoints ---


@router.post(
    "/zones/{zone_id}/sensors",
    response_model=SensorResponse,
    status_code=201,
    summary="Create a sensor in a zone",
    description=(
        "Create a new environmental sensor in a zone."
    ),
    responses={
        201: {"description": "Sensor created"},
        404: {"description": "Zone not found"},
        409: {"description": "Duplicate name"},
        422: {"description": "Validation error"},
    },
)
def create_sensor(
    zone_id: str,
    data: SensorCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.create_sensor(
        company_id=current_user.company_id,
        zone_id=uuid.UUID(zone_id),
        name=data.name,
        sensor_type=data.sensor_type.value,
        status=data.status.value,
        location_description=data.location_description,
    )


@router.get(
    "/zones/{zone_id}/sensors",
    response_model=SensorListResponse,
    summary="List sensors in a zone",
    description=(
        "List all sensors in a zone."
    ),
)
def list_sensors(
    zone_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: CoolingStatus | None = Query(
        None,
        description="Filter by status",
    ),
    sensor_type: SensorType | None = Query(
        None,
        description="Filter by sensor type",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
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
    service = CoolingService(db)
    return service.list_sensors(
        company_id=current_user.company_id,
        zone_id=uuid.UUID(zone_id),
        status=status.value if status else None,
        sensor_type=sensor_type.value
        if sensor_type
        else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/sensors/{sensor_id}",
    response_model=SensorResponse,
    summary="Get a sensor",
    description="Get details of a specific sensor.",
    responses={
        404: {"description": "Sensor not found"},
    },
)
def get_sensor(
    sensor_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.get_sensor(
        company_id=current_user.company_id,
        sensor_id=uuid.UUID(sensor_id),
    )


# --- Environmental Summary Endpoints ---


@router.get(
    "/rooms/{room_id}/environment-summary",
    response_model=RoomEnvironmentSummaryResponse,
    summary="Get room environment summary",
    description=(
        "Get environmental summary for a room "
        "including temperature, humidity, "
        "cooling status, and warnings."
    ),
    responses={
        404: {"description": "Room not found"},
    },
)
def get_room_environment(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.get_room_environment_summary(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
    )


@router.get(
    "/datacenters/{datacenter_id}/environment-summary",
    response_model=DataCenterEnvironmentSummaryResponse,
    summary="Get datacenter environment summary",
    description=(
        "Get environmental summary for a data center "
        "including average temperature/humidity, "
        "critical rooms, and failed cooling units."
    ),
    responses={
        404: {"description": "Data center not found"},
    },
)
def get_datacenter_environment(
    datacenter_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = CoolingService(db)
    return service.get_datacenter_environment_summary(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
    )
