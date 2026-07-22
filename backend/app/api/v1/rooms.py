import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.room import (
    RoomCreateRequest,
    RoomListResponse,
    RoomResponse,
    RoomStatus,
    RoomType,
    RoomUpdateRequest,
)
from app.services.room import RoomService

router = APIRouter(
    tags=["Rooms"],
)

WRITE_ROLES = ("OWNER", "ADMIN")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


@router.post(
    "/floors/{floor_id}/rooms",
    response_model=RoomResponse,
    status_code=201,
    summary="Create a room",
    description=(
        "Create a new room on a floor. "
        "Only OWNER and ADMIN roles can create."
    ),
    responses={
        201: {"description": "Room created"},
        404: {"description": "Floor not found"},
        409: {"description": "Duplicate name or code"},
        422: {"description": "Validation error"},
    },
)
def create_room(
    floor_id: str,
    data: RoomCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RoomService(db)
    return service.create(
        company_id=current_user.company_id,
        floor_id=uuid.UUID(floor_id),
        name=data.name,
        code=data.code,
        room_type=data.room_type.value,
        status=data.status.value,
        description=data.description,
        area_sqm=data.area_sqm,
        height_meters=data.height_meters,
        max_rack_capacity=data.max_rack_capacity,
        max_power_capacity_kw=data.max_power_capacity_kw,
        max_cooling_capacity_kw=(
            data.max_cooling_capacity_kw
        ),
        temperature_min=data.temperature_min,
        temperature_max=data.temperature_max,
        humidity_min=data.humidity_min,
        humidity_max=data.humidity_max,
    )


@router.get(
    "/floors/{floor_id}/rooms",
    response_model=RoomListResponse,
    summary="List rooms",
    description=(
        "List all rooms on a floor "
        "with filtering, sorting, and pagination."
    ),
)
def list_rooms(
    floor_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: RoomStatus | None = Query(
        None,
        description="Filter by status",
    ),
    room_type: RoomType | None = Query(
        None,
        description="Filter by room type",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
    ),
    sort_by: str = Query(
        "created_at",
        description=(
            "Sort field: name, code, room_type, "
            "status, created_at, updated_at"
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
    service = RoomService(db)
    return service.list_by_floor(
        company_id=current_user.company_id,
        floor_id=uuid.UUID(floor_id),
        status=status.value if status else None,
        room_type=room_type.value if room_type else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/rooms/{room_id}",
    response_model=RoomResponse,
    summary="Get a room",
    description=(
        "Get details of a specific room."
    ),
    responses={
        404: {"description": "Room not found"},
    },
)
def get_room(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RoomService(db)
    return service.get(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
    )


@router.patch(
    "/rooms/{room_id}",
    response_model=RoomResponse,
    summary="Update a room",
    description=(
        "Update a room. "
        "Only OWNER and ADMIN roles can update."
    ),
    responses={
        200: {"description": "Room updated"},
        404: {"description": "Room not found"},
        409: {"description": "Duplicate name or code"},
    },
)
def update_room(
    room_id: str,
    data: RoomUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RoomService(db)
    return service.update(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
        name=data.name,
        code=data.code,
        room_type=data.room_type.value
        if data.room_type
        else None,
        status=data.status.value if data.status else None,
        description=data.description,
        area_sqm=data.area_sqm,
        height_meters=data.height_meters,
        max_rack_capacity=data.max_rack_capacity,
        max_power_capacity_kw=data.max_power_capacity_kw,
        max_cooling_capacity_kw=(
            data.max_cooling_capacity_kw
        ),
        temperature_min=data.temperature_min,
        temperature_max=data.temperature_max,
        humidity_min=data.humidity_min,
        humidity_max=data.humidity_max,
    )


@router.delete(
    "/rooms/{room_id}",
    summary="Delete a room",
    description=(
        "Soft delete a room. "
        "Only OWNER and ADMIN roles can delete."
    ),
    responses={
        200: {"description": "Room deleted"},
        404: {"description": "Room not found"},
    },
)
def delete_room(
    room_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = RoomService(db)
    return service.delete(
        company_id=current_user.company_id,
        room_id=uuid.UUID(room_id),
    )
