import math
import uuid

from sqlalchemy.orm import Session

from app.repositories.ip_address import (
    IPAddressRepository,
)
from app.repositories.network_interface import (
    NetworkInterfaceRepository,
)
from app.repositories.physical_connection import (
    PhysicalConnectionRepository,
)
from app.repositories.subnet import SubnetRepository
from app.repositories.vlan import VLANRepository
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_INTERFACE_TYPES = {
    "ETHERNET",
    "FIBRE_CHANNEL",
    "MGMT",
    "LOOPBACK",
    "VLAN",
    "LAG",
}

VALID_INTERFACE_STATUSES = {"UP", "DOWN", "MAINTENANCE"}

VALID_CONNECTION_TYPES = {
    "COPPER",
    "FIBER",
    "DAC",
    "AOC",
}

VALID_CONNECTION_STATUSES = {
    "ACTIVE",
    "INACTIVE",
    "MAINTENANCE",
}

VALID_VLAN_STATUSES = {
    "ACTIVE",
    "INACTIVE",
    "RESERVED",
}

VALID_IP_STATUSES = {
    "AVAILABLE",
    "RESERVED",
    "ASSIGNED",
    "UNAVAILABLE",
}


class NetworkService:
    def __init__(self, db: Session):
        self.db = db
        self.interface_repo = NetworkInterfaceRepository(
            db
        )
        self.connection_repo = (
            PhysicalConnectionRepository(db)
        )
        self.vlan_repo = VLANRepository(db)
        self.subnet_repo = SubnetRepository(db)
        self.ip_repo = IPAddressRepository(db)

    def _serialize_interface(self, iface) -> dict:
        return {
            "id": str(iface.id),
            "company_id": str(iface.company_id),
            "device_id": str(iface.device_id),
            "name": iface.name,
            "interface_type": iface.interface_type,
            "status": iface.status,
            "mac_address": iface.mac_address,
            "ip_address": iface.ip_address,
            "speed_mbps": iface.speed_mbps,
            "description": iface.description,
            "created_at": iface.created_at.isoformat(),
            "updated_at": iface.updated_at.isoformat(),
        }

    def _serialize_connection(self, conn) -> dict:
        return {
            "id": str(conn.id),
            "company_id": str(conn.company_id),
            "source_interface_id": str(
                conn.source_interface_id
            ),
            "destination_interface_id": str(
                conn.destination_interface_id
            ),
            "connection_type": conn.connection_type,
            "cable_type": conn.cable_type,
            "length_meters": conn.length_meters,
            "status": conn.status,
            "created_at": conn.created_at.isoformat(),
            "updated_at": conn.updated_at.isoformat(),
        }

    def _serialize_vlan(self, vlan) -> dict:
        return {
            "id": str(vlan.id),
            "company_id": str(vlan.company_id),
            "datacenter_id": str(vlan.datacenter_id),
            "name": vlan.name,
            "vlan_id": vlan.vlan_id,
            "description": vlan.description,
            "status": vlan.status,
            "created_at": vlan.created_at.isoformat(),
            "updated_at": vlan.updated_at.isoformat(),
        }

    def _serialize_subnet(self, subnet) -> dict:
        return {
            "id": str(subnet.id),
            "company_id": str(subnet.company_id),
            "vlan_id": str(subnet.vlan_id),
            "network_address": subnet.network_address,
            "cidr": subnet.cidr,
            "gateway": subnet.gateway,
            "description": subnet.description,
            "created_at": subnet.created_at.isoformat(),
            "updated_at": subnet.updated_at.isoformat(),
        }

    def _serialize_ip(self, ip) -> dict:
        return {
            "id": str(ip.id),
            "company_id": str(ip.company_id),
            "subnet_id": str(ip.subnet_id),
            "device_interface_id": (
                str(ip.device_interface_id)
                if ip.device_interface_id
                else None
            ),
            "address": ip.address,
            "status": ip.status,
            "description": ip.description,
            "created_at": ip.created_at.isoformat(),
            "updated_at": ip.updated_at.isoformat(),
        }

    # --- Interface Methods ---

    def create_interface(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        name: str,
        interface_type: str = "ETHERNET",
        status: str = "UP",
        mac_address: str | None = None,
        ip_address: str | None = None,
        speed_mbps: int | None = None,
        description: str | None = None,
    ) -> dict:
        if interface_type not in VALID_INTERFACE_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid interface_type: "
                    f"{interface_type}. Must be one of: "
                    f"{', '.join(sorted(VALID_INTERFACE_TYPES))}"
                )
            )

        if status not in VALID_INTERFACE_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_INTERFACE_STATUSES))}"
                )
            )

        existing = (
            self.interface_repo.get_by_device_and_name(
                device_id, name
            )
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "An interface with this name "
                    "already exists on this device"
                )
            )

        if mac_address:
            existing_mac = (
                self.interface_repo.get_by_mac_address(
                    mac_address
                )
            )
            if existing_mac:
                raise DuplicateException(
                    detail=(
                        "An interface with this MAC "
                        "address already exists"
                    )
                )

        iface = self.interface_repo.create(
            company_id=company_id,
            device_id=device_id,
            name=name,
            interface_type=interface_type,
            status=status,
            mac_address=mac_address,
            ip_address=ip_address,
            speed_mbps=speed_mbps,
            description=description,
        )

        self.db.commit()
        self.db.refresh(iface)

        return self._serialize_interface(iface)

    def get_interface(
        self,
        company_id: uuid.UUID,
        interface_id: uuid.UUID,
    ) -> dict:
        iface = (
            self.interface_repo.get_active_by_company_and_id(
                company_id, interface_id
            )
        )

        if not iface:
            raise NotFoundException(
                detail="Network interface not found"
            )

        return self._serialize_interface(iface)

    def list_interfaces(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        status: str | None = None,
        interface_type: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_INTERFACE_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}"
                    )
                )

        if interface_type is not None:
            if interface_type not in VALID_INTERFACE_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid interface_type filter: "
                        f"{interface_type}"
                    )
                )

        items, total = self.interface_repo.list_by_device(
            company_id=company_id,
            device_id=device_id,
            status=status,
            interface_type=interface_type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "interfaces": [
                self._serialize_interface(i) for i in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_interface(
        self,
        company_id: uuid.UUID,
        interface_id: uuid.UUID,
        name: str | None = None,
        interface_type: str | None = None,
        status: str | None = None,
        mac_address: str | None = None,
        ip_address: str | None = None,
        speed_mbps: int | None = None,
        description: str | None = None,
    ) -> dict:
        iface = (
            self.interface_repo.get_active_by_company_and_id(
                company_id, interface_id
            )
        )

        if not iface:
            raise NotFoundException(
                detail="Network interface not found"
            )

        if status is not None:
            if status not in VALID_INTERFACE_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        if interface_type is not None:
            if interface_type not in VALID_INTERFACE_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid interface_type: "
                        f"{interface_type}"
                    )
                )

        if name is not None and name != iface.name:
            existing = (
                self.interface_repo.get_by_device_and_name(
                    iface.device_id, name
                )
            )
            if existing and existing.id != iface.id:
                raise DuplicateException(
                    detail=(
                        "An interface with this name "
                        "already exists on this device"
                    )
                )

        if (
            mac_address is not None
            and mac_address != iface.mac_address
        ):
            if mac_address:
                existing_mac = (
                    self.interface_repo.get_by_mac_address(
                        mac_address
                    )
                )
                if existing_mac and existing_mac.id != iface.id:
                    raise DuplicateException(
                        detail=(
                            "An interface with this MAC "
                            "address already exists"
                        )
                    )

        self.interface_repo.update(
            iface,
            name=name,
            interface_type=interface_type,
            status=status,
            mac_address=mac_address,
            ip_address=ip_address,
            speed_mbps=speed_mbps,
            description=description,
        )

        self.db.commit()
        self.db.refresh(iface)

        return self._serialize_interface(iface)

    def delete_interface(
        self,
        company_id: uuid.UUID,
        interface_id: uuid.UUID,
    ) -> dict:
        iface = (
            self.interface_repo.get_active_by_company_and_id(
                company_id, interface_id
            )
        )

        if not iface:
            raise NotFoundException(
                detail="Network interface not found"
            )

        existing_conn = (
            self.connection_repo.get_by_interface(
                interface_id
            )
        )
        if existing_conn:
            raise ValidationException(
                detail=(
                    "Cannot delete interface with "
                    "existing connections. Remove "
                    "connections first."
                )
            )

        self.interface_repo.soft_delete(iface)
        self.db.commit()

        return {
            "message": (
                "Network interface deleted successfully"
            )
        }

    # --- Connection Methods ---

    def create_connection(
        self,
        company_id: uuid.UUID,
        source_interface_id: uuid.UUID,
        destination_interface_id: uuid.UUID,
        connection_type: str = "COPPER",
        cable_type: str | None = None,
        length_meters: int | None = None,
        status: str = "ACTIVE",
    ) -> dict:
        if connection_type not in VALID_CONNECTION_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid connection_type: "
                    f"{connection_type}. Must be one of: "
                    f"{', '.join(sorted(VALID_CONNECTION_TYPES))}"
                )
            )

        if status not in VALID_CONNECTION_STATUSES:
            raise ValidationException(
                detail=f"Invalid status: {status}"
            )

        if (
            source_interface_id == destination_interface_id
        ):
            raise ValidationException(
                detail=(
                    "Source and destination interfaces "
                    "must be different"
                )
            )

        src_iface = (
            self.interface_repo.get_active_by_company_and_id(
                company_id, source_interface_id
            )
        )
        if not src_iface:
            raise NotFoundException(
                detail="Source interface not found"
            )

        dst_iface = (
            self.interface_repo.get_active_by_company_and_id(
                company_id, destination_interface_id
            )
        )
        if not dst_iface:
            raise NotFoundException(
                detail="Destination interface not found"
            )

        if (
            src_iface.device_id == dst_iface.device_id
        ):
            raise ValidationException(
                detail=(
                    "Cannot connect two interfaces "
                    "on the same device"
                )
            )

        existing = (
            self.connection_repo.get_by_interfaces(
                source_interface_id,
                destination_interface_id,
            )
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A connection between these "
                    "interfaces already exists"
                )
            )

        reverse = (
            self.connection_repo.get_by_interfaces(
                destination_interface_id,
                source_interface_id,
            )
        )
        if reverse:
            raise DuplicateException(
                detail=(
                    "A connection between these "
                    "interfaces already exists"
                )
            )

        src_conn = self.connection_repo.get_by_interface(
            source_interface_id
        )
        if src_conn:
            raise ValidationException(
                detail=(
                    "Source interface already has "
                    "a connection"
                )
            )

        dst_conn = self.connection_repo.get_by_interface(
            destination_interface_id
        )
        if dst_conn:
            raise ValidationException(
                detail=(
                    "Destination interface already has "
                    "a connection"
                )
            )

        conn = self.connection_repo.create(
            company_id=company_id,
            source_interface_id=source_interface_id,
            destination_interface_id=(
                destination_interface_id
            ),
            connection_type=connection_type,
            cable_type=cable_type,
            length_meters=length_meters,
            status=status,
        )

        self.db.commit()
        self.db.refresh(conn)

        return self._serialize_connection(conn)

    def get_connection(
        self,
        company_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> dict:
        conn = (
            self.connection_repo.get_active_by_company_and_id(
                company_id, connection_id
            )
        )

        if not conn:
            raise NotFoundException(
                detail="Connection not found"
            )

        return self._serialize_connection(conn)

    def list_connections(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        connection_type: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_CONNECTION_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status filter: {status}"
                )

        if connection_type is not None:
            if connection_type not in VALID_CONNECTION_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid connection_type filter: "
                        f"{connection_type}"
                    )
                )

        items, total = (
            self.connection_repo.list_by_company(
                company_id=company_id,
                status=status,
                connection_type=connection_type,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                size=size,
            )
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "connections": [
                self._serialize_connection(c)
                for c in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_connection(
        self,
        company_id: uuid.UUID,
        connection_id: uuid.UUID,
        connection_type: str | None = None,
        cable_type: str | None = None,
        length_meters: int | None = None,
        status: str | None = None,
    ) -> dict:
        conn = (
            self.connection_repo.get_active_by_company_and_id(
                company_id, connection_id
            )
        )

        if not conn:
            raise NotFoundException(
                detail="Connection not found"
            )

        if status is not None:
            if status not in VALID_CONNECTION_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        if connection_type is not None:
            if connection_type not in VALID_CONNECTION_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid connection_type: "
                        f"{connection_type}"
                    )
                )

        self.connection_repo.update(
            conn,
            connection_type=connection_type,
            cable_type=cable_type,
            length_meters=length_meters,
            status=status,
        )

        self.db.commit()
        self.db.refresh(conn)

        return self._serialize_connection(conn)

    def delete_connection(
        self,
        company_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> dict:
        conn = (
            self.connection_repo.get_active_by_company_and_id(
                company_id, connection_id
            )
        )

        if not conn:
            raise NotFoundException(
                detail="Connection not found"
            )

        self.connection_repo.soft_delete(conn)
        self.db.commit()

        return {
            "message": (
                "Connection deleted successfully"
            )
        }

    # --- VLAN Methods ---

    def create_vlan(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        name: str,
        vlan_id: int,
        description: str | None = None,
        status: str = "ACTIVE",
    ) -> dict:
        if status not in VALID_VLAN_STATUSES:
            raise ValidationException(
                detail=f"Invalid status: {status}"
            )

        existing_name = (
            self.vlan_repo.get_by_datacenter_and_name(
                datacenter_id, name
            )
        )
        if existing_name:
            raise DuplicateException(
                detail=(
                    "A VLAN with this name "
                    "already exists in this datacenter"
                )
            )

        existing_vlan_id = (
            self.vlan_repo.get_by_company_and_vlan_id(
                company_id, vlan_id
            )
        )
        if existing_vlan_id:
            raise DuplicateException(
                detail=(
                    "A VLAN with this VLAN ID "
                    "already exists in this company"
                )
            )

        vlan = self.vlan_repo.create(
            company_id=company_id,
            datacenter_id=datacenter_id,
            name=name,
            vlan_id=vlan_id,
            description=description,
            status=status,
        )

        self.db.commit()
        self.db.refresh(vlan)

        return self._serialize_vlan(vlan)

    def get_vlan(
        self,
        company_id: uuid.UUID,
        vlan_id: uuid.UUID,
    ) -> dict:
        vlan = (
            self.vlan_repo.get_active_by_company_and_id(
                company_id, vlan_id
            )
        )

        if not vlan:
            raise NotFoundException(
                detail="VLAN not found"
            )

        return self._serialize_vlan(vlan)

    def list_vlans(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_VLAN_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status filter: {status}"
                )

        items, total = (
            self.vlan_repo.list_by_datacenter(
                company_id=company_id,
                datacenter_id=datacenter_id,
                status=status,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                size=size,
            )
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "vlans": [
                self._serialize_vlan(v) for v in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_vlan(
        self,
        company_id: uuid.UUID,
        vlan_uuid: uuid.UUID,
        name: str | None = None,
        vlan_id: int | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict:
        vlan = (
            self.vlan_repo.get_active_by_company_and_id(
                company_id, vlan_uuid
            )
        )

        if not vlan:
            raise NotFoundException(
                detail="VLAN not found"
            )

        if status is not None:
            if status not in VALID_VLAN_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        if name is not None and name != vlan.name:
            existing = (
                self.vlan_repo.get_by_datacenter_and_name(
                    vlan.datacenter_id, name
                )
            )
            if existing and existing.id != vlan.id:
                raise DuplicateException(
                    detail=(
                        "A VLAN with this name "
                        "already exists in this datacenter"
                    )
                )

        if (
            vlan_id is not None
            and vlan_id != vlan.vlan_id
        ):
            existing_vid = (
                self.vlan_repo.get_by_company_and_vlan_id(
                    company_id, vlan_id
                )
            )
            if existing_vid and existing_vid.id != vlan.id:
                raise DuplicateException(
                    detail=(
                        "A VLAN with this VLAN ID "
                        "already exists in this company"
                    )
                )

        self.vlan_repo.update(
            vlan,
            name=name,
            vlan_id=vlan_id,
            description=description,
            status=status,
        )

        self.db.commit()
        self.db.refresh(vlan)

        return self._serialize_vlan(vlan)

    def delete_vlan(
        self,
        company_id: uuid.UUID,
        vlan_id: uuid.UUID,
    ) -> dict:
        vlan = (
            self.vlan_repo.get_active_by_company_and_id(
                company_id, vlan_id
            )
        )

        if not vlan:
            raise NotFoundException(
                detail="VLAN not found"
            )

        self.vlan_repo.soft_delete(vlan)
        self.db.commit()

        return {
            "message": "VLAN deleted successfully"
        }

    # --- Subnet Methods ---

    def create_subnet(
        self,
        company_id: uuid.UUID,
        vlan_id: uuid.UUID,
        network_address: str,
        cidr: int,
        gateway: str | None = None,
        description: str | None = None,
    ) -> dict:
        vlan = (
            self.vlan_repo.get_active_by_company_and_id(
                company_id, vlan_id
            )
        )
        if not vlan:
            raise NotFoundException(
                detail="VLAN not found"
            )

        existing = (
            self.subnet_repo.get_by_company_and_network(
                company_id, network_address, cidr
            )
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A subnet with this network "
                    "address already exists"
                )
            )

        subnet = self.subnet_repo.create(
            company_id=company_id,
            vlan_id=vlan_id,
            network_address=network_address,
            cidr=cidr,
            gateway=gateway,
            description=description,
        )

        self.db.commit()
        self.db.refresh(subnet)

        return self._serialize_subnet(subnet)

    def get_subnet(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
    ) -> dict:
        subnet = (
            self.subnet_repo.get_active_by_company_and_id(
                company_id, subnet_id
            )
        )

        if not subnet:
            raise NotFoundException(
                detail="Subnet not found"
            )

        return self._serialize_subnet(subnet)

    def list_subnets(
        self,
        company_id: uuid.UUID,
        vlan_id: uuid.UUID,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        items, total = self.subnet_repo.list_by_vlan(
            company_id=company_id,
            vlan_id=vlan_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "subnets": [
                self._serialize_subnet(s) for s in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_subnet(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
        network_address: str | None = None,
        cidr: int | None = None,
        gateway: str | None = None,
        description: str | None = None,
    ) -> dict:
        subnet = (
            self.subnet_repo.get_active_by_company_and_id(
                company_id, subnet_id
            )
        )

        if not subnet:
            raise NotFoundException(
                detail="Subnet not found"
            )

        self.subnet_repo.update(
            subnet,
            network_address=network_address,
            cidr=cidr,
            gateway=gateway,
            description=description,
        )

        self.db.commit()
        self.db.refresh(subnet)

        return self._serialize_subnet(subnet)

    def delete_subnet(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
    ) -> dict:
        subnet = (
            self.subnet_repo.get_active_by_company_and_id(
                company_id, subnet_id
            )
        )

        if not subnet:
            raise NotFoundException(
                detail="Subnet not found"
            )

        self.subnet_repo.soft_delete(subnet)
        self.db.commit()

        return {
            "message": "Subnet deleted successfully"
        }

    # --- IP Address Methods ---

    def create_ip(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
        address: str,
        device_interface_id: uuid.UUID | None = None,
        status: str = "AVAILABLE",
        description: str | None = None,
    ) -> dict:
        if status not in VALID_IP_STATUSES:
            raise ValidationException(
                detail=f"Invalid status: {status}"
            )

        subnet = (
            self.subnet_repo.get_active_by_company_and_id(
                company_id, subnet_id
            )
        )
        if not subnet:
            raise NotFoundException(
                detail="Subnet not found"
            )

        existing = (
            self.ip_repo.get_by_company_and_address(
                company_id, address
            )
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "An IP address with this address "
                    "already exists"
                )
            )

        if device_interface_id is not None:
            iface = (
                self.interface_repo.get_active_by_company_and_id(
                    company_id, device_interface_id
                )
            )
            if not iface:
                raise NotFoundException(
                    detail="Network interface not found"
                )
            if status != "ASSIGNED":
                status = "ASSIGNED"

        ip = self.ip_repo.create(
            company_id=company_id,
            subnet_id=subnet_id,
            address=address,
            device_interface_id=device_interface_id,
            status=status,
            description=description,
        )

        self.db.commit()
        self.db.refresh(ip)

        return self._serialize_ip(ip)

    def get_ip(
        self,
        company_id: uuid.UUID,
        ip_id: uuid.UUID,
    ) -> dict:
        ip = (
            self.ip_repo.get_active_by_company_and_id(
                company_id, ip_id
            )
        )

        if not ip:
            raise NotFoundException(
                detail="IP address not found"
            )

        return self._serialize_ip(ip)

    def list_ips(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_IP_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status filter: {status}"
                )

        items, total = self.ip_repo.list_by_subnet(
            company_id=company_id,
            subnet_id=subnet_id,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "ip_addresses": [
                self._serialize_ip(i) for i in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_ip(
        self,
        company_id: uuid.UUID,
        ip_id: uuid.UUID,
        device_interface_id: str | None = None,
        address: str | None = None,
        status: str | None = None,
        description: str | None = None,
    ) -> dict:
        ip = (
            self.ip_repo.get_active_by_company_and_id(
                company_id, ip_id
            )
        )

        if not ip:
            raise NotFoundException(
                detail="IP address not found"
            )

        if status is not None:
            if status not in VALID_IP_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        if (
            address is not None
            and address != ip.address
        ):
            existing = (
                self.ip_repo.get_by_company_and_address(
                    company_id, address
                )
            )
            if existing and existing.id != ip.id:
                raise DuplicateException(
                    detail=(
                        "An IP address with this address "
                        "already exists"
                    )
                )

        resolved_interface_id = None
        if device_interface_id is not None:
            if device_interface_id == "":
                resolved_interface_id = uuid.UUID(
                    "00000000-0000-0000-0000-000000000000"
                )
            else:
                resolved_interface_id = uuid.UUID(
                    device_interface_id
                )

        self.ip_repo.update(
            ip,
            device_interface_id=resolved_interface_id,
            address=address,
            status=status,
            description=description,
        )

        self.db.commit()
        self.db.refresh(ip)

        return self._serialize_ip(ip)

    def delete_ip(
        self,
        company_id: uuid.UUID,
        ip_id: uuid.UUID,
    ) -> dict:
        ip = (
            self.ip_repo.get_active_by_company_and_id(
                company_id, ip_id
            )
        )

        if not ip:
            raise NotFoundException(
                detail="IP address not found"
            )

        self.ip_repo.soft_delete(ip)
        self.db.commit()

        return {
            "message": (
                "IP address deleted successfully"
            )
        }

    # --- Network Map Engine ---

    def get_network_map(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID | None = None,
    ) -> dict:
        connections = (
            self.connection_repo.list_all_by_company(
                company_id
            )
        )

        interface_ids = set()
        for conn in connections:
            interface_ids.add(conn.source_interface_id)
            interface_ids.add(
                conn.destination_interface_id
            )

        if not interface_ids:
            return {
                "nodes": [],
                "edges": [],
                "total_nodes": 0,
                "total_edges": len(connections),
            }

        from app.models.network_interface import (
            NetworkInterface,
        )

        interfaces = (
            self.db.query(NetworkInterface)
            .filter(
                NetworkInterface.id.in_(interface_ids),
                NetworkInterface.deleted_at.is_(None),
            )
            .all()
        )

        device_ids = set()
        interface_to_device = {}
        for iface in interfaces:
            device_ids.add(iface.device_id)
            interface_to_device[iface.id] = iface

        if not device_ids:
            return {
                "nodes": [],
                "edges": [],
                "total_nodes": 0,
                "total_edges": len(connections),
            }

        from app.models.device import Device

        device_query = self.db.query(Device).filter(
            Device.id.in_(device_ids),
            Device.deleted_at.is_(None),
        )

        if datacenter_id is not None:
            from app.models.rack import Rack

            racks = (
                self.db.query(Rack)
                .filter(
                    Rack.datacenter_id == datacenter_id,
                    Rack.deleted_at.is_(None),
                )
                .all()
            )
            rack_ids = [r.id for r in racks]
            device_query = device_query.filter(
                Device.rack_id.in_(rack_ids)
            )

        devices = device_query.all()

        device_map = {d.id: d for d in devices}

        nodes = []
        for device_id in device_ids:
            device = device_map.get(device_id)
            if not device:
                continue

            device_connections = [
                c
                for c in connections
                if interface_to_device.get(
                    c.source_interface_id
                )
                and interface_to_device[
                    c.source_interface_id
                ].device_id
                == device_id
                or interface_to_device.get(
                    c.destination_interface_id
                )
                and interface_to_device[
                    c.destination_interface_id
                ].device_id
                == device_id
            ]

            connected_device_ids = set()
            for c in device_connections:
                src = interface_to_device.get(
                    c.source_interface_id
                )
                dst = interface_to_device.get(
                    c.destination_interface_id
                )
                if src and src.device_id != device_id:
                    connected_device_ids.add(
                        str(src.device_id)
                    )
                if dst and dst.device_id != device_id:
                    connected_device_ids.add(
                        str(dst.device_id)
                    )

            nodes.append({
                "node_id": str(device.id),
                "node_type": "DEVICE",
                "name": device.name,
                "status": device.status,
                "connections": sorted(
                    connected_device_ids
                ),
            })

        edges = []
        for conn in connections:
            edges.append({
                "source_interface_id": str(
                    conn.source_interface_id
                ),
                "destination_interface_id": str(
                    conn.destination_interface_id
                ),
                "connection_type": conn.connection_type,
                "status": conn.status,
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }
