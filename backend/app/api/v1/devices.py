import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.device import (
    CheckPlacementRequest,
    CheckPlacementResponse,
    DeviceCreateRequest,
    DeviceListResponse,
    DeviceResponse,
    DeviceStatus,
    DeviceType,
    DeviceUpdateRequest,
    RackLayoutResponse,
)
from app.services.device import DeviceService

router = APIRouter(
    tags=["Devices"],
)

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


@router.post(
    "/racks/{rack_id}/devices",
    response_model=DeviceResponse,
    status_code=201,
    summary="Create a device in a rack",
    description=(
        "Create a new device and mount it in a rack. "
        "Validates rack placement, power capacity, "
        "and uniqueness constraints."
    ),
    responses={
        201: {"description": "Device created"},
        404: {"description": "Rack not found"},
        409: {
            "description": (
                "Duplicate name, serial number, "
                "or asset tag"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_device(
    rack_id: str,
    data: DeviceCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    return service.create(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
        name=data.name,
        hostname=data.hostname,
        device_type=data.device_type.value,
        status=data.status.value,
        vendor=data.vendor,
        model=data.model,
        serial_number=data.serial_number,
        asset_tag=data.asset_tag,
        description=data.description,
        rack_unit_start=data.rack_unit_start,
        rack_unit_height=data.rack_unit_height,
        front_or_rear=data.front_or_rear,
        ip_address=data.ip_address,
        mac_address=data.mac_address,
        management_ip=data.management_ip,
        operating_system=data.operating_system,
        cpu=data.cpu,
        memory_gb=data.memory_gb,
        storage_gb=data.storage_gb,
        power_consumption_watt=(
            data.power_consumption_watt
        ),
        purchase_date=data.purchase_date,
        warranty_end_date=data.warranty_end_date,
    )


@router.get(
    "/racks/{rack_id}/devices",
    response_model=DeviceListResponse,
    summary="List devices in a rack",
    description=(
        "List all devices in a rack "
        "with filtering, sorting, and pagination."
    ),
)
def list_devices(
    rack_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    device_type: DeviceType | None = Query(
        None,
        description="Filter by device type",
    ),
    status: DeviceStatus | None = Query(
        None,
        description="Filter by status",
    ),
    vendor: str | None = Query(
        None,
        description="Filter by vendor",
    ),
    search: str | None = Query(
        None,
        description=(
            "Search by name, hostname, "
            "serial number, or asset tag"
        ),
    ),
    sort_by: str = Query(
        "created_at",
        description=(
            "Sort field: name, hostname, device_type, "
            "status, vendor, serial_number, asset_tag, "
            "rack_unit_start, rack_unit_height, "
            "power_consumption_watt, "
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
    service = DeviceService(db)
    return service.list_by_rack(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
        device_type=device_type.value
        if device_type
        else None,
        status=status.value if status else None,
        vendor=vendor,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/devices/{device_id}",
    response_model=DeviceResponse,
    summary="Get a device",
    description=(
        "Get details of a specific device."
    ),
    responses={
        404: {"description": "Device not found"},
    },
)
def get_device(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    return service.get(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
    )


@router.patch(
    "/devices/{device_id}",
    response_model=DeviceResponse,
    summary="Update a device",
    description=(
        "Update a device. "
        "OWNER, ADMIN, and ENGINEER roles can update."
    ),
    responses={
        200: {"description": "Device updated"},
        404: {"description": "Device not found"},
        409: {
            "description": (
                "Duplicate name, serial number, "
                "or asset tag"
            )
        },
    },
)
def update_device(
    device_id: str,
    data: DeviceUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    return service.update(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
        name=data.name,
        hostname=data.hostname,
        device_type=data.device_type.value
        if data.device_type
        else None,
        status=data.status.value
        if data.status
        else None,
        vendor=data.vendor,
        model=data.model,
        serial_number=data.serial_number,
        asset_tag=data.asset_tag,
        description=data.description,
        rack_unit_start=data.rack_unit_start,
        rack_unit_height=data.rack_unit_height,
        front_or_rear=data.front_or_rear,
        ip_address=data.ip_address,
        mac_address=data.mac_address,
        management_ip=data.management_ip,
        operating_system=data.operating_system,
        cpu=data.cpu,
        memory_gb=data.memory_gb,
        storage_gb=data.storage_gb,
        power_consumption_watt=(
            data.power_consumption_watt
        ),
        purchase_date=data.purchase_date,
        warranty_end_date=data.warranty_end_date,
    )


@router.delete(
    "/devices/{device_id}",
    summary="Delete a device",
    description=(
        "Soft delete a device. "
        "OWNER, ADMIN, and ENGINEER roles can delete."
    ),
    responses={
        200: {"description": "Device deleted"},
        404: {"description": "Device not found"},
    },
)
def delete_device(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    return service.delete(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
    )


@router.get(
    "/racks/{rack_id}/layout",
    response_model=RackLayoutResponse,
    summary="Get rack layout",
    description=(
        "Return the physical layout of a rack "
        "showing all unit positions and which "
        "devices occupy them."
    ),
    responses={
        404: {"description": "Rack not found"},
    },
)
def get_rack_layout(
    rack_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    return service.get_rack_layout(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
    )


@router.post(
    "/racks/{rack_id}/check-placement",
    response_model=CheckPlacementResponse,
    summary="Check device placement",
    description=(
        "Validate if a device can be placed at "
        "the specified rack units without overlap."
    ),
    responses={
        404: {"description": "Rack not found"},
    },
)
def check_placement(
    rack_id: str,
    data: CheckPlacementRequest,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = DeviceService(db)
    return service.check_placement(
        company_id=current_user.company_id,
        rack_id=uuid.UUID(rack_id),
        rack_unit_start=data.rack_unit_start,
        rack_unit_height=data.rack_unit_height,
        device_id=data.device_id,
    )
