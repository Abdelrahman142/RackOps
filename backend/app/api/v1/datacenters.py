import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.datacenter import (
    DataCenterCreateRequest,
    DataCenterListResponse,
    DataCenterResponse,
    DataCenterStatus,
    DataCenterUpdateRequest,
)
from app.services.datacenter import DataCenterService

router = APIRouter(
    prefix="/datacenters",
    tags=["Data Centers"],
)

WRITE_ROLES = ("OWNER", "ADMIN")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


@router.post(
    "",
    response_model=DataCenterResponse,
    status_code=201,
    summary="Create a data center",
    description=(
        "Create a new data center within the "
        "authenticated user's company. "
        "Only OWNER and ADMIN roles can create."
    ),
    responses={
        201: {
            "description": "Data center created"
        },
        409: {
            "description": (
                "Duplicate name or code"
            )
        },
        422: {
            "description": "Validation error"
        },
    },
)
def create_datacenter(
    data: DataCenterCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DataCenterService(db)
    return service.create(
        company_id=current_user.company_id,
        name=data.name,
        code=data.code,
        country=data.country,
        city=data.city,
        address=data.address,
        timezone=data.timezone,
        status=data.status.value,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
    )


@router.get(
    "",
    response_model=DataCenterListResponse,
    summary="List data centers",
    description=(
        "List all data centers in the "
        "authenticated user's company with "
        "filtering, sorting, and pagination."
    ),
)
def list_datacenters(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: DataCenterStatus | None = Query(
        None,
        description="Filter by status",
    ),
    country: str | None = Query(
        None,
        description="Filter by country",
    ),
    city: str | None = Query(
        None,
        description="Filter by city",
    ),
    search: str | None = Query(
        None,
        description="Search by name",
    ),
    sort_by: str = Query(
        "created_at",
        description=(
            "Sort field: name, code, status, "
            "country, city, created_at, updated_at"
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
    service = DataCenterService(db)
    return service.list(
        company_id=current_user.company_id,
        status=status.value if status else None,
        country=country,
        city=city,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/{datacenter_id}",
    response_model=DataCenterResponse,
    summary="Get a data center",
    description=(
        "Get details of a specific data center "
        "within the authenticated user's company."
    ),
    responses={
        404: {
            "description": "Data center not found"
        },
    },
)
def get_datacenter(
    datacenter_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DataCenterService(db)
    return service.get(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
    )


@router.patch(
    "/{datacenter_id}",
    response_model=DataCenterResponse,
    summary="Update a data center",
    description=(
        "Update a data center within the "
        "authenticated user's company. "
        "Only OWNER and ADMIN roles can update."
    ),
    responses={
        200: {
            "description": "Data center updated"
        },
        404: {
            "description": "Data center not found"
        },
        409: {
            "description": (
                "Duplicate name or code"
            )
        },
    },
)
def update_datacenter(
    datacenter_id: str,
    data: DataCenterUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DataCenterService(db)
    return service.update(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
        name=data.name,
        code=data.code,
        country=data.country,
        city=data.city,
        address=data.address,
        timezone=data.timezone,
        status=data.status.value
        if data.status
        else None,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
    )


@router.delete(
    "/{datacenter_id}",
    summary="Delete a data center",
    description=(
        "Soft delete a data center within the "
        "authenticated user's company. "
        "Only OWNER and ADMIN roles can delete."
    ),
    responses={
        200: {
            "description": "Data center deleted"
        },
        404: {
            "description": "Data center not found"
        },
    },
)
def delete_datacenter(
    datacenter_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DataCenterService(db)
    return service.delete(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
    )
