import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.network import (
    IPAddressCreateRequest,
    IPAddressListResponse,
    IPAddressResponse,
    IPAddressUpdateRequest,
    NetworkInterfaceCreateRequest,
    NetworkInterfaceListResponse,
    NetworkInterfaceResponse,
    NetworkInterfaceUpdateRequest,
    NetworkMapResponse,
    PhysicalConnectionCreateRequest,
    PhysicalConnectionListResponse,
    PhysicalConnectionResponse,
    PhysicalConnectionUpdateRequest,
    SubnetCreateRequest,
    SubnetListResponse,
    SubnetResponse,
    SubnetUpdateRequest,
    VLANCreateRequest,
    VLANListResponse,
    VLANResponse,
    VLANUpdateRequest,
)
from app.services.network import NetworkService

router = APIRouter(
    tags=["Network Topology & Connectivity"],
)

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


# --- Network Interface Endpoints ---


@router.post(
    "/devices/{device_id}/interfaces",
    response_model=NetworkInterfaceResponse,
    status_code=201,
    summary="Create a network interface on a device",
    description=(
        "Create a new network interface (eth0, "
        "FC0/0, mgmt0, etc.) on a device."
    ),
    responses={
        201: {"description": "Interface created"},
        404: {"description": "Device not found"},
        409: {
            "description": (
                "Duplicate name or MAC address"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_interface(
    device_id: str,
    data: NetworkInterfaceCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.create_interface(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
        name=data.name,
        interface_type=data.interface_type,
        status=data.status,
        mac_address=data.mac_address,
        ip_address=data.ip_address,
        speed_mbps=data.speed_mbps,
        description=data.description,
    )


@router.get(
    "/devices/{device_id}/interfaces",
    response_model=NetworkInterfaceListResponse,
    summary="List network interfaces on a device",
    description=(
        "List all network interfaces on a device "
        "with filtering, sorting, and pagination."
    ),
)
def list_interfaces(
    device_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    interface_type: str | None = Query(
        None,
        description="Filter by interface type",
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
    service = NetworkService(db)
    return service.list_interfaces(
        company_id=current_user.company_id,
        device_id=uuid.UUID(device_id),
        status=status,
        interface_type=interface_type,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/interfaces/{interface_id}",
    response_model=NetworkInterfaceResponse,
    summary="Get a network interface",
    description="Get details of a specific network interface.",
    responses={
        404: {"description": "Interface not found"},
    },
)
def get_interface(
    interface_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.get_interface(
        company_id=current_user.company_id,
        interface_id=uuid.UUID(interface_id),
    )


@router.patch(
    "/interfaces/{interface_id}",
    response_model=NetworkInterfaceResponse,
    summary="Update a network interface",
    description="Update a network interface.",
    responses={
        200: {"description": "Interface updated"},
        404: {"description": "Interface not found"},
        409: {
            "description": (
                "Duplicate name or MAC address"
            )
        },
    },
)
def update_interface(
    interface_id: str,
    data: NetworkInterfaceUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.update_interface(
        company_id=current_user.company_id,
        interface_id=uuid.UUID(interface_id),
        name=data.name,
        interface_type=data.interface_type,
        status=data.status,
        mac_address=data.mac_address,
        ip_address=data.ip_address,
        speed_mbps=data.speed_mbps,
        description=data.description,
    )


@router.delete(
    "/interfaces/{interface_id}",
    summary="Delete a network interface",
    description="Soft delete a network interface.",
    responses={
        200: {"description": "Interface deleted"},
        404: {"description": "Interface not found"},
        422: {
            "description": (
                "Interface has existing connections"
            )
        },
    },
)
def delete_interface(
    interface_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.delete_interface(
        company_id=current_user.company_id,
        interface_id=uuid.UUID(interface_id),
    )


# --- Physical Connection Endpoints ---


@router.post(
    "/connections",
    response_model=PhysicalConnectionResponse,
    status_code=201,
    summary="Create a physical connection",
    description=(
        "Create a physical cable connection between "
        "two network interfaces."
    ),
    responses={
        201: {"description": "Connection created"},
        404: {"description": "Interface not found"},
        409: {
            "description": (
                "Connection already exists or "
                "interface already connected"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_connection(
    data: PhysicalConnectionCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.create_connection(
        company_id=current_user.company_id,
        source_interface_id=uuid.UUID(
            data.source_interface_id
        ),
        destination_interface_id=uuid.UUID(
            data.destination_interface_id
        ),
        connection_type=data.connection_type,
        cable_type=data.cable_type,
        length_meters=data.length_meters,
        status=data.status,
    )


@router.get(
    "/connections",
    response_model=PhysicalConnectionListResponse,
    summary="List physical connections",
    description=(
        "List all physical connections with "
        "filtering, sorting, and pagination."
    ),
)
def list_connections(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    connection_type: str | None = Query(
        None,
        description="Filter by connection type",
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
    service = NetworkService(db)
    return service.list_connections(
        company_id=current_user.company_id,
        status=status,
        connection_type=connection_type,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/connections/{connection_id}",
    response_model=PhysicalConnectionResponse,
    summary="Get a physical connection",
    description=(
        "Get details of a specific physical connection."
    ),
    responses={
        404: {"description": "Connection not found"},
    },
)
def get_connection(
    connection_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.get_connection(
        company_id=current_user.company_id,
        connection_id=uuid.UUID(connection_id),
    )


@router.patch(
    "/connections/{connection_id}",
    response_model=PhysicalConnectionResponse,
    summary="Update a physical connection",
    description="Update a physical connection.",
    responses={
        200: {"description": "Connection updated"},
        404: {"description": "Connection not found"},
    },
)
def update_connection(
    connection_id: str,
    data: PhysicalConnectionUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.update_connection(
        company_id=current_user.company_id,
        connection_id=uuid.UUID(connection_id),
        connection_type=data.connection_type,
        cable_type=data.cable_type,
        length_meters=data.length_meters,
        status=data.status,
    )


@router.delete(
    "/connections/{connection_id}",
    summary="Delete a physical connection",
    description="Soft delete a physical connection.",
    responses={
        200: {"description": "Connection deleted"},
        404: {"description": "Connection not found"},
    },
)
def delete_connection(
    connection_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.delete_connection(
        company_id=current_user.company_id,
        connection_id=uuid.UUID(connection_id),
    )


# --- VLAN Endpoints ---


@router.post(
    "/datacenters/{datacenter_id}/vlans",
    response_model=VLANResponse,
    status_code=201,
    summary="Create a VLAN in a datacenter",
    description=(
        "Create a new VLAN in a data center."
    ),
    responses={
        201: {"description": "VLAN created"},
        404: {"description": "Datacenter not found"},
        409: {
            "description": (
                "Duplicate name or VLAN ID"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_vlan(
    datacenter_id: str,
    data: VLANCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.create_vlan(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
        name=data.name,
        vlan_id=data.vlan_id,
        description=data.description,
        status=data.status,
    )


@router.get(
    "/datacenters/{datacenter_id}/vlans",
    response_model=VLANListResponse,
    summary="List VLANs in a datacenter",
    description=(
        "List all VLANs in a data center "
        "with filtering, sorting, and pagination."
    ),
)
def list_vlans(
    datacenter_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
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
    service = NetworkService(db)
    return service.list_vlans(
        company_id=current_user.company_id,
        datacenter_id=uuid.UUID(datacenter_id),
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/vlans/{vlan_id}",
    response_model=VLANResponse,
    summary="Get a VLAN",
    description="Get details of a specific VLAN.",
    responses={
        404: {"description": "VLAN not found"},
    },
)
def get_vlan(
    vlan_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.get_vlan(
        company_id=current_user.company_id,
        vlan_id=uuid.UUID(vlan_id),
    )


@router.patch(
    "/vlans/{vlan_id}",
    response_model=VLANResponse,
    summary="Update a VLAN",
    description="Update a VLAN.",
    responses={
        200: {"description": "VLAN updated"},
        404: {"description": "VLAN not found"},
        409: {
            "description": (
                "Duplicate name or VLAN ID"
            )
        },
    },
)
def update_vlan(
    vlan_id: str,
    data: VLANUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.update_vlan(
        company_id=current_user.company_id,
        vlan_uuid=uuid.UUID(vlan_id),
        name=data.name,
        vlan_id=data.vlan_id,
        description=data.description,
        status=data.status,
    )


@router.delete(
    "/vlans/{vlan_id}",
    summary="Delete a VLAN",
    description="Soft delete a VLAN.",
    responses={
        200: {"description": "VLAN deleted"},
        404: {"description": "VLAN not found"},
    },
)
def delete_vlan(
    vlan_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.delete_vlan(
        company_id=current_user.company_id,
        vlan_id=uuid.UUID(vlan_id),
    )


# --- Subnet Endpoints ---


@router.post(
    "/vlans/{vlan_id}/subnets",
    response_model=SubnetResponse,
    status_code=201,
    summary="Create a subnet in a VLAN",
    description=(
        "Create a new subnet within a VLAN."
    ),
    responses={
        201: {"description": "Subnet created"},
        404: {"description": "VLAN not found"},
        409: {
            "description": (
                "Duplicate network address"
            )
        },
        422: {"description": "Validation error"},
    },
)
def create_subnet(
    vlan_id: str,
    data: SubnetCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.create_subnet(
        company_id=current_user.company_id,
        vlan_id=uuid.UUID(vlan_id),
        network_address=data.network_address,
        cidr=data.cidr,
        gateway=data.gateway,
        description=data.description,
    )


@router.get(
    "/vlans/{vlan_id}/subnets",
    response_model=SubnetListResponse,
    summary="List subnets in a VLAN",
    description=(
        "List all subnets within a VLAN."
    ),
)
def list_subnets(
    vlan_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    search: str | None = Query(
        None,
        description="Search by network address",
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
    service = NetworkService(db)
    return service.list_subnets(
        company_id=current_user.company_id,
        vlan_id=uuid.UUID(vlan_id),
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/subnets/{subnet_id}",
    response_model=SubnetResponse,
    summary="Get a subnet",
    description="Get details of a specific subnet.",
    responses={
        404: {"description": "Subnet not found"},
    },
)
def get_subnet(
    subnet_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.get_subnet(
        company_id=current_user.company_id,
        subnet_id=uuid.UUID(subnet_id),
    )


@router.patch(
    "/subnets/{subnet_id}",
    response_model=SubnetResponse,
    summary="Update a subnet",
    description="Update a subnet.",
    responses={
        200: {"description": "Subnet updated"},
        404: {"description": "Subnet not found"},
    },
)
def update_subnet(
    subnet_id: str,
    data: SubnetUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.update_subnet(
        company_id=current_user.company_id,
        subnet_id=uuid.UUID(subnet_id),
        network_address=data.network_address,
        cidr=data.cidr,
        gateway=data.gateway,
        description=data.description,
    )


@router.delete(
    "/subnets/{subnet_id}",
    summary="Delete a subnet",
    description="Soft delete a subnet.",
    responses={
        200: {"description": "Subnet deleted"},
        404: {"description": "Subnet not found"},
    },
)
def delete_subnet(
    subnet_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.delete_subnet(
        company_id=current_user.company_id,
        subnet_id=uuid.UUID(subnet_id),
    )


# --- IP Address Endpoints ---


@router.post(
    "/subnets/{subnet_id}/ips",
    response_model=IPAddressResponse,
    status_code=201,
    summary="Create an IP address in a subnet",
    description=(
        "Create a new IP address within a subnet."
    ),
    responses={
        201: {"description": "IP address created"},
        404: {"description": "Subnet not found"},
        409: {
            "description": "Duplicate IP address"
        },
        422: {"description": "Validation error"},
    },
)
def create_ip(
    subnet_id: str,
    data: IPAddressCreateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.create_ip(
        company_id=current_user.company_id,
        subnet_id=uuid.UUID(subnet_id),
        address=data.address,
        device_interface_id=(
            uuid.UUID(data.device_interface_id)
            if data.device_interface_id
            else None
        ),
        status=data.status,
        description=data.description,
    )


@router.get(
    "/subnets/{subnet_id}/ips",
    response_model=IPAddressListResponse,
    summary="List IP addresses in a subnet",
    description=(
        "List all IP addresses within a subnet."
    ),
)
def list_ips(
    subnet_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    status: str | None = Query(
        None,
        description="Filter by status",
    ),
    search: str | None = Query(
        None,
        description="Search by address",
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
    service = NetworkService(db)
    return service.list_ips(
        company_id=current_user.company_id,
        subnet_id=uuid.UUID(subnet_id),
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/ips/{ip_id}",
    response_model=IPAddressResponse,
    summary="Get an IP address",
    description="Get details of a specific IP address.",
    responses={
        404: {"description": "IP address not found"},
    },
)
def get_ip(
    ip_id: str,
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.get_ip(
        company_id=current_user.company_id,
        ip_id=uuid.UUID(ip_id),
    )


@router.patch(
    "/ips/{ip_id}",
    response_model=IPAddressResponse,
    summary="Update an IP address",
    description="Update an IP address.",
    responses={
        200: {"description": "IP address updated"},
        404: {"description": "IP address not found"},
        409: {"description": "Duplicate IP address"},
    },
)
def update_ip(
    ip_id: str,
    data: IPAddressUpdateRequest,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.update_ip(
        company_id=current_user.company_id,
        ip_id=uuid.UUID(ip_id),
        device_interface_id=data.device_interface_id,
        address=data.address,
        status=data.status,
        description=data.description,
    )


@router.delete(
    "/ips/{ip_id}",
    summary="Delete an IP address",
    description="Soft delete an IP address.",
    responses={
        200: {"description": "IP address deleted"},
        404: {"description": "IP address not found"},
    },
)
def delete_ip(
    ip_id: str,
    current_user: User = Depends(
        RequireRole(*WRITE_ROLES)
    ),
    db: Session = Depends(get_db),
):
    service = NetworkService(db)
    return service.delete_ip(
        company_id=current_user.company_id,
        ip_id=uuid.UUID(ip_id),
    )


# --- Network Map Endpoint ---


@router.get(
    "/network-map",
    response_model=NetworkMapResponse,
    summary="Get network topology map",
    description=(
        "Get the full network topology map showing "
        "devices as nodes and physical connections "
        "as edges."
    ),
)
def get_network_map(
    current_user: User = Depends(
        RequireRole(*READ_ROLES)
    ),
    db: Session = Depends(get_db),
    datacenter_id: str | None = Query(
        None,
        description="Filter by datacenter",
    ),
):
    service = NetworkService(db)
    return service.get_network_map(
        company_id=current_user.company_id,
        datacenter_id=(
            uuid.UUID(datacenter_id)
            if datacenter_id
            else None
        ),
    )
