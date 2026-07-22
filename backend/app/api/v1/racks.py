import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.rack import (
    RackCapacityResponse,
    RackCreateRequest,
    RackListResponse,
    RackResponse,
    RackStatus,
    RackType,
    RackUpdateRequest,
)
from app.services.rack import RackService

router = APIRouter(
    tags=["Racks"],
)

WRITE_ROLES = ("OWNER", "ADMIN")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


@router.post(
    "/rooms/{room_id}/racks",
    response_model=RackResponse,
    status_code=201,
    summary="Create a rack",
    description=(
        "Create a new rack in a room. "
        "Only OWNER and ADMIN roles can create."
    ),
    responses={
        201: {"description": "Rack created"},
        404: {"description": "Room not found"},
        409: {
            "description": (
                "Duplicate name, code, or serial number"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_rack(
    room_id: str,
    data: RackCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RackService(db)
    return service.create(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        name=data.name,
        code=data.code,
        rack_type=data.rack_type.value,
        status=data.status.value,
        height_units=data.height_units,
        width_mm=data.width_mm,
        depth_mm=data.depth_mm,
        max_weight_kg=data.max_weight_kg,
        current_weight_kg=data.current_weight_kg,
        power_capacity_kw=data.power_capacity_kw,
        current_power_usage_kw=(
            data.current_power_usage_kw
        ),
        cooling_capacity_kw=data.cooling_capacity_kw,
        manufacturer=data.manufacturer,
        model=data.model,
        serial_number=data.serial_number,
        position_in_room=data.position_in_room,
        description=data.description,
    )


@router.get(
    "/rooms/{room_id}/racks",
    response_model=RackListResponse,
    summary="List racks in a room",
    description=(
        "List all racks in a room "
        "with filtering, sorting, and pagination."
    ),
)
def list_racks(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: RackStatus | None = Query(
        None,
        description="Filter by status",
    ),
    rack_type: RackType | None = Query(
        None,
        description="Filter by rack type",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
    ),
    sort_by: str = Query(
        "created_at",
        description=(
            "Sort field: name, code, rack_type, "
            "status, height_units, position_in_room, "
            "created_at, updated_at"
        ),
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
        description="Items per page (1-100)",
    ),
):
    service = RackService(db)
    return service.list_by_room(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        status=status.value if status else None,
        rack_type=rack_type.value if rack_type else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/racks/{rack_id}",
    response_model=RackResponse,
    summary="Get a rack",
    description=(
        "Get details of a specific rack."
    ),
    responses={
        404: {"description": "Rack not found"},
    },
)
def get_rack(
    rack_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RackService(db)
    return service.get(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
    )


@router.get(
    "/racks/{rack_id}/capacity",
    response_model=RackCapacityResponse,
    summary="Get rack capacity",
    description=(
        "Get capacity information for a rack."
    ),
    responses={
        404: {"description": "Rack not found"},
    },
)
def get_rack_capacity(
    rack_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RackService(db)
    return service.get_capacity(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
    )


@router.patch(
    "/racks/{rack_id}",
    response_model=RackResponse,
    summary="Update a rack",
    description=(
        "Update a rack. "
        "Only OWNER and ADMIN roles can update."
    ),
    responses={
        200: {"description": "Rack updated"},
        404: {"description": "Rack not found"},
        409: {
            "description": (
                "Duplicate name, code, or serial number"
            )
        },
    },
)
def update_rack(
    rack_id: str,
    data: RackUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RackService(db)
    return service.update(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
        name=data.name,
        code=data.code,
        rack_type=data.rack_type.value
        if data.rack_type
        else None,
        status=data.status.value if data.status else None,
        height_units=data.height_units,
        width_mm=data.width_mm,
        depth_mm=data.depth_mm,
        max_weight_kg=data.max_weight_kg,
        current_weight_kg=data.current_weight_kg,
        power_capacity_kw=data.power_capacity_kw,
        current_power_usage_kw=(
            data.current_power_usage_kw
        ),
        cooling_capacity_kw=data.cooling_capacity_kw,
        manufacturer=data.manufacturer,
        model=data.model,
        serial_number=data.serial_number,
        position_in_room=data.position_in_room,
        description=data.description,
    )


@router.delete(
    "/racks/{rack_id}",
    summary="Delete a rack",
    description=(
        "Soft delete a rack. "
        "Only OWNER and ADMIN roles can delete."
    ),
    responses={
        200: {"description": "Rack deleted"},
        404: {"description": "Rack not found"},
    },
)
def delete_rack(
    rack_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RackService(db)
    return service.delete(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
    )
