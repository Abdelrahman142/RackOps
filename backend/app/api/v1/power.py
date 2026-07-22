import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.power import (
    DataCenterPowerSummaryResponse,
    PDuresponse,
    PDUCreateRequest,
    PDUListResponse,
    PDUUpdateRequest,
    PowerFeedCreateRequest,
    PowerFeedListResponse,
    PowerFeedResponse,
    PowerFeedUpdateRequest,
    PowerStatus,
    RackPowerResponse,
    RoomPowerSummaryResponse,
    UPSCreateRequest,
    UPSListResponse,
    UPSResponse,
    UPSUpdateRequest,
)
from app.services.power import PowerService

router = APIRouter(
    tags=["Power Management"],
)

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


# --- UPS Endpoints ---


@router.post(
    "/rooms/{room_id}/ups",
    response_model=UPSResponse,
    status_code=201,
    summary="Create a UPS in a room",
    description=(
        "Create a new UPS system in a room."
    ),
    responses={
        201: {"description": "UPS created"},
        404: {"description": "Room not found"},
        409: {"description": "Duplicate name or serial"},
        422: {"description": "Validation error"},
    },
)
def create_ups(
    room_id: str,
    data: UPSCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.create_ups(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        name=data.name,
        capacity_kva=data.capacity_kva,
        model=data.model,
        manufacturer=data.manufacturer,
        serial_number=data.serial_number,
        status=data.status.value,
        battery_capacity_minutes=(
            data.battery_capacity_minutes
        ),
        input_voltage=data.input_voltage,
        output_voltage=data.output_voltage,
        efficiency_percent=data.efficiency_percent,
    )


@router.get(
    "/rooms/{room_id}/ups",
    response_model=UPSListResponse,
    summary="List UPS systems in a room",
    description=(
        "List all UPS systems in a room "
        "with filtering and pagination."
    ),
)
def list_ups(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: PowerStatus | None = Query(
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
    service = PowerService(db)
    return service.list_ups(
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
    "/ups/{ups_id}",
    response_model=UPSResponse,
    summary="Get a UPS",
    description="Get details of a specific UPS.",
    responses={
        404: {"description": "UPS not found"},
    },
)
def get_ups(
    ups_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.get_ups(
        company_id=current_user.company_id,
        ups_id=uuid.UUID(ups_id),
    )


@router.patch(
    "/ups/{ups_id}",
    response_model=UPSResponse,
    summary="Update a UPS",
    description="Update a UPS system.",
    responses={
        200: {"description": "UPS updated"},
        404: {"description": "UPS not found"},
        409: {"description": "Duplicate name or serial"},
    },
)
def update_ups(
    ups_id: str,
    data: UPSUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.update_ups(
        company_id=current_user.company_id,
        ups_id=uuid.UUID(ups_id),
        name=data.name,
        model=data.model,
        manufacturer=data.manufacturer,
        serial_number=data.serial_number,
        status=data.status.value if data.status else None,
        capacity_kva=data.capacity_kva,
        battery_capacity_minutes=(
            data.battery_capacity_minutes
        ),
        input_voltage=data.input_voltage,
        output_voltage=data.output_voltage,
        efficiency_percent=data.efficiency_percent,
    )


@router.delete(
    "/ups/{ups_id}",
    summary="Delete a UPS",
    description="Soft delete a UPS system.",
    responses={
        200: {"description": "UPS deleted"},
        404: {"description": "UPS not found"},
    },
)
def delete_ups(
    ups_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.delete_ups(
        company_id=current_user.company_id,
        ups_id=uuid.UUID(ups_id),
    )


# --- PDU Endpoints ---


@router.post(
    "/rooms/{room_id}/pdus",
    response_model=PDuresponse,
    status_code=201,
    summary="Create a PDU in a room",
    description=(
        "Create a new PDU in a room. "
        "Optionally associate with a rack."
    ),
    responses={
        201: {"description": "PDU created"},
        404: {"description": "Room or rack not found"},
        409: {"description": "Duplicate name or serial"},
        422: {"description": "Validation error"},
    },
)
def create_pdu(
    room_id: str,
    data: PDUCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.create_pdu(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        name=data.name,
        total_capacity_amp=data.total_capacity_amp,
        model=data.model,
        manufacturer=data.manufacturer,
        serial_number=data.serial_number,
        status=data.status.value,
        rack_id=data.rack_id,
        current_usage_amp=data.current_usage_amp,
        phase_type=data.phase_type.value,
    )


@router.get(
    "/rooms/{room_id}/pdus",
    response_model=PDUListResponse,
    summary="List PDUs in a room",
    description=(
        "List all PDUs in a room "
        "with filtering and pagination."
    ),
)
def list_pdus(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: PowerStatus | None = Query(
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
    service = PowerService(db)
    return service.list_pdus(
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
    "/pdus/{pdu_id}",
    response_model=PDuresponse,
    summary="Get a PDU",
    description="Get details of a specific PDU.",
    responses={
        404: {"description": "PDU not found"},
    },
)
def get_pdu(
    pdu_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.get_pdu(
        company_id=current_user.company_id,
        pdu_id=uuid.UUID(pdu_id),
    )


@router.patch(
    "/pdus/{pdu_id}",
    response_model=PDuresponse,
    summary="Update a PDU",
    description="Update a PDU.",
    responses={
        200: {"description": "PDU updated"},
        404: {"description": "PDU not found"},
        409: {"description": "Duplicate name or serial"},
    },
)
def update_pdu(
    pdu_id: str,
    data: PDUUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.update_pdu(
        company_id=current_user.company_id,
        pdu_id=uuid.UUID(pdu_id),
        name=data.name,
        model=data.model,
        manufacturer=data.manufacturer,
        serial_number=data.serial_number,
        status=data.status.value if data.status else None,
        rack_id=data.rack_id,
        total_capacity_amp=data.total_capacity_amp,
        current_usage_amp=data.current_usage_amp,
        phase_type=data.phase_type.value
        if data.phase_type
        else None,
    )


@router.delete(
    "/pdus/{pdu_id}",
    summary="Delete a PDU",
    description="Soft delete a PDU.",
    responses={
        200: {"description": "PDU deleted"},
        404: {"description": "PDU not found"},
    },
)
def delete_pdu(
    pdu_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.delete_pdu(
        company_id=current_user.company_id,
        pdu_id=uuid.UUID(pdu_id),
    )


# --- PowerFeed Endpoints ---


@router.post(
    "/power-feeds",
    response_model=PowerFeedResponse,
    status_code=201,
    summary="Create a power feed",
    description=(
        "Create a power feed connection "
        "between source and destination."
    ),
    responses={
        201: {"description": "Power feed created"},
        404: {"description": "Source or destination not found"},
        409: {"description": "Duplicate connection"},
        422: {"description": "Validation error"},
    },
)
def create_feed(
    data: PowerFeedCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.create_feed(
        company_id=current_user.company_id,
        source_type=data.source_type.value,
        source_id=data.source_id,
        destination_type=data.destination_type.value,
        destination_id=data.destination_id,
        voltage=data.voltage,
        amp_rating=data.amp_rating,
        status=data.status.value,
    )


@router.get(
    "/power-feeds",
    response_model=PowerFeedListResponse,
    summary="List power feeds",
    description=(
        "List all power feeds for the company."
    ),
)
def list_feeds(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    source_type: str | None = Query(
        None,
        description="Filter by source type",
    ),
    destination_type: str | None = Query(
        None,
        description="Filter by destination type",
    ),
    status: PowerStatus | None = Query(
        None,
        description="Filter by status",
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
    service = PowerService(db)
    return service.list_feeds(
        company_id=current_user.company_id,
        source_type=source_type,
        destination_type=destination_type,
        status=status.value if status else None,
        page=page,
        size=size,
    )


@router.get(
    "/power-feeds/{feed_id}",
    response_model=PowerFeedResponse,
    summary="Get a power feed",
    description="Get details of a specific power feed.",
    responses={
        404: {"description": "Power feed not found"},
    },
)
def get_feed(
    feed_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.get_feed(
        company_id=current_user.company_id,
        feed_id=uuid.UUID(feed_id),
    )


@router.patch(
    "/power-feeds/{feed_id}",
    response_model=PowerFeedResponse,
    summary="Update a power feed",
    description="Update a power feed.",
    responses={
        200: {"description": "Power feed updated"},
        404: {"description": "Power feed not found"},
    },
)
def update_feed(
    feed_id: str,
    data: PowerFeedUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.update_feed(
        company_id=current_user.company_id,
        feed_id=uuid.UUID(feed_id),
        voltage=data.voltage,
        amp_rating=data.amp_rating,
        status=data.status.value if data.status else None,
    )


@router.delete(
    "/power-feeds/{feed_id}",
    summary="Delete a power feed",
    description="Soft delete a power feed.",
    responses={
        200: {"description": "Power feed deleted"},
        404: {"description": "Power feed not found"},
    },
)
def delete_feed(
    feed_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.delete_feed(
        company_id=current_user.company_id,
        feed_id=uuid.UUID(feed_id),
    )


# --- Power Summary Endpoints ---


@router.get(
    "/racks/{rack_id}/power",
    response_model=RackPowerResponse,
    summary="Get rack power summary",
    description=(
        "Get power summary for a rack "
        "including device power and PDU details."
    ),
    responses={
        404: {"description": "Rack not found"},
    },
)
def get_rack_power(
    rack_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.get_rack_power(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
    )


@router.get(
    "/rooms/{room_id}/power",
    response_model=RoomPowerSummaryResponse,
    summary="Get room power summary",
    description=(
        "Get power summary for a room "
        "including UPS, PDU, and device power totals."
    ),
    responses={
        404: {"description": "Room not found"},
    },
)
def get_room_power(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.get_room_power_summary(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
    )


@router.get(
    "/datacenters/{datacenter_id}/power",
    response_model=DataCenterPowerSummaryResponse,
    summary="Get datacenter power summary",
    description=(
        "Get power summary for a data center "
        "including all rooms."
    ),
    responses={
        404: {"description": "Data center not found"},
    },
)
def get_datacenter_power(
    datacenter_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = PowerService(db)
    return service.get_datacenter_power_summary(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
    )
