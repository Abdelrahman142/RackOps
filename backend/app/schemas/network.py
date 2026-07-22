from pydantic import BaseModel, Field


# --- Network Interface Schemas ---


class NetworkInterfaceCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Interface name",
        examples=["eth0"],
    )
    interface_type: str = Field(
        default="ETHERNET",
        description="Interface type",
    )
    status: str = Field(
        default="UP",
        description="Interface status",
    )
    mac_address: str | None = Field(
        None,
        max_length=17,
        description="MAC address (globally unique)",
    )
    ip_address: str | None = Field(
        None,
        max_length=45,
        description="IP address",
    )
    speed_mbps: int | None = Field(
        None,
        ge=0,
        description="Speed in Mbps",
    )
    description: str | None = Field(
        None,
        description="Description",
    )


class NetworkInterfaceUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    interface_type: str | None = None
    status: str | None = None
    mac_address: str | None = Field(
        None,
        max_length=17,
    )
    ip_address: str | None = Field(
        None,
        max_length=45,
    )
    speed_mbps: int | None = Field(
        None,
        ge=0,
    )
    description: str | None = None


class NetworkInterfaceResponse(BaseModel):
    id: str
    company_id: str
    device_id: str
    name: str
    interface_type: str
    status: str
    mac_address: str | None
    ip_address: str | None
    speed_mbps: int | None
    description: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class NetworkInterfaceListResponse(BaseModel):
    interfaces: list[NetworkInterfaceResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Physical Connection Schemas ---


class PhysicalConnectionCreateRequest(BaseModel):
    source_interface_id: str = Field(
        ...,
        description="Source interface UUID",
    )
    destination_interface_id: str = Field(
        ...,
        description="Destination interface UUID",
    )
    connection_type: str = Field(
        default="COPPER",
        description="Connection type",
    )
    cable_type: str | None = Field(
        None,
        max_length=30,
        description="Cable type",
    )
    length_meters: int | None = Field(
        None,
        ge=0,
        description="Cable length in meters",
    )
    status: str = Field(
        default="ACTIVE",
        description="Connection status",
    )


class PhysicalConnectionUpdateRequest(BaseModel):
    connection_type: str | None = None
    cable_type: str | None = Field(
        None,
        max_length=30,
    )
    length_meters: int | None = Field(
        None,
        ge=0,
    )
    status: str | None = None


class PhysicalConnectionResponse(BaseModel):
    id: str
    company_id: str
    source_interface_id: str
    destination_interface_id: str
    connection_type: str
    cable_type: str | None
    length_meters: int | None
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PhysicalConnectionListResponse(BaseModel):
    connections: list[PhysicalConnectionResponse]
    total: int
    page: int
    size: int
    pages: int


# --- VLAN Schemas ---


class VLANCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="VLAN name",
        examples=["Production-VLAN"],
    )
    vlan_id: int = Field(
        ...,
        ge=1,
        le=4094,
        description="VLAN tag (1-4094)",
    )
    description: str | None = Field(
        None,
        description="VLAN description",
    )
    status: str = Field(
        default="ACTIVE",
        description="VLAN status",
    )


class VLANUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    vlan_id: int | None = Field(
        None,
        ge=1,
        le=4094,
    )
    description: str | None = None
    status: str | None = None


class VLANResponse(BaseModel):
    id: str
    company_id: str
    datacenter_id: str
    name: str
    vlan_id: int
    description: str | None
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class VLANListResponse(BaseModel):
    vlans: list[VLANResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Subnet Schemas ---


class SubnetCreateRequest(BaseModel):
    network_address: str = Field(
        ...,
        max_length=45,
        description="Network address",
        examples=["192.168.1.0"],
    )
    cidr: int = Field(
        ...,
        ge=0,
        le=128,
        description="CIDR prefix length",
    )
    gateway: str | None = Field(
        None,
        max_length=45,
        description="Gateway IP address",
    )
    description: str | None = Field(
        None,
        description="Subnet description",
    )


class SubnetUpdateRequest(BaseModel):
    network_address: str | None = Field(
        None,
        max_length=45,
    )
    cidr: int | None = Field(
        None,
        ge=0,
        le=128,
    )
    gateway: str | None = Field(
        None,
        max_length=45,
    )
    description: str | None = None


class SubnetResponse(BaseModel):
    id: str
    company_id: str
    vlan_id: str
    network_address: str
    cidr: int
    gateway: str | None
    description: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SubnetListResponse(BaseModel):
    subnets: list[SubnetResponse]
    total: int
    page: int
    size: int
    pages: int


# --- IP Address Schemas ---


class IPAddressCreateRequest(BaseModel):
    device_interface_id: str | None = Field(
        None,
        description=(
            "Network interface UUID to assign to"
        ),
    )
    address: str = Field(
        ...,
        max_length=45,
        description="IP address",
    )
    status: str = Field(
        default="AVAILABLE",
        description="IP status",
    )
    description: str | None = Field(
        None,
        description="IP description",
    )


class IPAddressUpdateRequest(BaseModel):
    device_interface_id: str | None = None
    address: str | None = Field(
        None,
        max_length=45,
    )
    status: str | None = None
    description: str | None = None


class IPAddressResponse(BaseModel):
    id: str
    company_id: str
    subnet_id: str
    device_interface_id: str | None
    address: str
    status: str
    description: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class IPAddressListResponse(BaseModel):
    ip_addresses: list[IPAddressResponse]
    total: int
    page: int
    size: int
    pages: int


# --- Network Map Schemas ---


class NetworkMapNodeResponse(BaseModel):
    node_id: str
    node_type: str
    name: str
    status: str | None
    connections: list[str]


class NetworkMapEdgeResponse(BaseModel):
    source_interface_id: str
    destination_interface_id: str
    connection_type: str
    status: str


class NetworkMapResponse(BaseModel):
    nodes: list[NetworkMapNodeResponse]
    edges: list[NetworkMapEdgeResponse]
    total_nodes: int
    total_edges: int
