import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.building import (
    BuildingCreateRequest,
    BuildingListResponse,
    BuildingResponse,
    BuildingStatus,
    BuildingUpdateRequest,
)
from app.services.building import BuildingService

router = APIRouter(
    tags=["Buildings"],
)

WRITE_ROLES = ("OWNER", "ADMIN")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


@router.post(
    "/datacenters/{datacenter_id}/buildings",
    response_model=BuildingResponse,
    status_code=201,
    summary="Create a building",
    description=(
        "Create a new building within a data center. "
        "Only OWNER and ADMIN roles can create."
    ),
    responses={
        201: {"description": "Building created"},
        404: {"description": "Data center not found"},
        409: {"description": "Duplicate name or code"},
        422: {"description": "Validation error"},
    },
)
def create_building(
    datacenter_id: str,
    data: BuildingCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = BuildingService(db)
    return service.create(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
        name=data.name,
        code=data.code,
        address=data.address,
        status=data.status.value,
        description=data.description,
        number_of_floors=data.number_of_floors,
        total_area=data.total_area,
        power_capacity_kw=data.power_capacity_kw,
        cooling_capacity_kw=data.cooling_capacity_kw,
    )


@router.get(
    "/datacenters/{datacenter_id}/buildings",
    response_model=BuildingListResponse,
    summary="List buildings",
    description=(
        "List all buildings in a data center "
        "with filtering, sorting, and pagination."
    ),
)
def list_buildings(
    datacenter_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: BuildingStatus | None = Query(
        None,
        description="Filter by status",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
    ),
    sort_by: str = Query(
        "created_at",
        description=(
            "Sort field: name, code, status, "
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
    service = BuildingService(db)
    return service.list_by_datacenter(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
        status=status.value if status else None,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/buildings/{building_id}",
    response_model=BuildingResponse,
    summary="Get a building",
    description=(
        "Get details of a specific building."
    ),
    responses={
        404: {"description": "Building not found"},
    },
)
def get_building(
    building_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = BuildingService(db)
    return service.get(
        company_id=current_user.company_id,
        building_id=uuid.UUID(building_id),
    )


@router.patch(
    "/buildings/{building_id}",
    response_model=BuildingResponse,
    summary="Update a building",
    description=(
        "Update a building. "
        "Only OWNER and ADMIN roles can update."
    ),
    responses={
        200: {"description": "Building updated"},
        404: {"description": "Building not found"},
        409: {"description": "Duplicate name or code"},
    },
)
def update_building(
    building_id: str,
    data: BuildingUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = BuildingService(db)
    return service.update(
        company_id=current_user.company_id,
        building_id=uuid.UUID(building_id),
        name=data.name,
        code=data.code,
        address=data.address,
        status=data.status.value if data.status else None,
        description=data.description,
        number_of_floors=data.number_of_floors,
        total_area=data.total_area,
        power_capacity_kw=data.power_capacity_kw,
        cooling_capacity_kw=data.cooling_capacity_kw,
    )


@router.delete(
    "/buildings/{building_id}",
    summary="Delete a building",
    description=(
        "Soft delete a building. "
        "Only OWNER and ADMIN roles can delete."
    ),
    responses={
        200: {"description": "Building deleted"},
        404: {"description": "Building not found"},
    },
)
def delete_building(
    building_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = BuildingService(db)
    return service.delete(
        company_id=current_user.company_id,
        building_id=uuid.UUID(building_id),
    )
