import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.floor import (
    FloorCreateRequest,
    FloorListResponse,
    FloorResponse,
    FloorStatus,
    FloorUpdateRequest,
)
from app.services.floor import FloorService

router = APIRouter(
    tags=["Floors"],
)

WRITE_ROLES = ("OWNER", "ADMIN")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


@router.post(
    "/buildings/{building_id}/floors",
    response_model=FloorResponse,
    status_code=201,
    summary="Create a floor",
    description=(
        "Create a new floor within a building. "
        "Only OWNER and ADMIN roles can create."
    ),
    responses={
        201: {"description": "Floor created"},
        404: {"description": "Building not found"},
        409: {
            "description": (
                "Duplicate name, code, or floor number"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_floor(
    building_id: str,
    data: FloorCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = FloorService(db)
    return service.create(
        company_id=current_user.company_id,
        building_id=uuid.UUID(building_id),
        name=data.name,
        code=data.code,
        floor_number=data.floor_number,
        status=data.status.value,
        description=data.description,
        total_area_sqm=data.total_area_sqm,
        max_power_capacity_kw=data.max_power_capacity_kw,
        max_cooling_capacity_kw=(
            data.max_cooling_capacity_kw
        ),
    )


@router.get(
    "/buildings/{building_id}/floors",
    response_model=FloorListResponse,
    summary="List floors",
    description=(
        "List all floors in a building "
        "with filtering, sorting, and pagination."
    ),
)
def list_floors(
    building_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: FloorStatus | None = Query(
        None,
        description="Filter by status",
    ),
    floor_number: int | None = Query(
        None,
        description="Filter by floor number",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
    ),
    sort_by: str = Query(
        "created_at",
        description=(
            "Sort field: name, code, floor_number, "
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
    service = FloorService(db)
    return service.list_by_building(
        company_id=current_user.company_id,
        building_id=uuid.UUID(building_id),
        status=status.value if status else None,
        floor_number=floor_number,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/floors/{floor_id}",
    response_model=FloorResponse,
    summary="Get a floor",
    description=(
        "Get details of a specific floor."
    ),
    responses={
        404: {"description": "Floor not found"},
    },
)
def get_floor(
    floor_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = FloorService(db)
    return service.get(
        company_id=current_user.company_id,
        floor_id=uuid.UUID(floor_id),
    )


@router.patch(
    "/floors/{floor_id}",
    response_model=FloorResponse,
    summary="Update a floor",
    description=(
        "Update a floor. "
        "Only OWNER and ADMIN roles can update."
    ),
    responses={
        200: {"description": "Floor updated"},
        404: {"description": "Floor not found"},
        409: {
            "description": (
                "Duplicate name, code, or floor number"
            )
        },
    },
)
def update_floor(
    floor_id: str,
    data: FloorUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = FloorService(db)
    return service.update(
        company_id=current_user.company_id,
        floor_id=uuid.UUID(floor_id),
        name=data.name,
        code=data.code,
        floor_number=data.floor_number,
        status=data.status.value if data.status else None,
        description=data.description,
        total_area_sqm=data.total_area_sqm,
        max_power_capacity_kw=data.max_power_capacity_kw,
        max_cooling_capacity_kw=(
            data.max_cooling_capacity_kw
        ),
    )


@router.delete(
    "/floors/{floor_id}",
    summary="Delete a floor",
    description=(
        "Soft delete a floor. "
        "Only OWNER and ADMIN roles can delete."
    ),
    responses={
        200: {"description": "Floor deleted"},
        404: {"description": "Floor not found"},
    },
)
def delete_floor(
    floor_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = FloorService(db)
    return service.delete(
        company_id=current_user.company_id,
        floor_id=uuid.UUID(floor_id),
    )
