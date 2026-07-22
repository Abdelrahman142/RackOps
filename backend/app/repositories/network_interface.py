import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.network_interface import (
    NetworkInterface,
)


class NetworkInterfaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
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
    ) -> NetworkInterface:
        interface = NetworkInterface(
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
        self.db.add(interface)
        self.db.flush()
        return interface

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        interface_id: uuid.UUID,
    ) -> NetworkInterface | None:
        return (
            self.db.query(NetworkInterface)
            .filter(
                NetworkInterface.id == interface_id,
                NetworkInterface.company_id == company_id,
                NetworkInterface.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_device_and_name(
        self,
        device_id: uuid.UUID,
        name: str,
    ) -> NetworkInterface | None:
        return (
            self.db.query(NetworkInterface)
            .filter(
                NetworkInterface.device_id == device_id,
                NetworkInterface.name == name,
                NetworkInterface.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_mac_address(
        self,
        mac_address: str,
    ) -> NetworkInterface | None:
        return (
            self.db.query(NetworkInterface)
            .filter(
                NetworkInterface.mac_address == mac_address,
                NetworkInterface.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_device(
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
    ) -> tuple[list[NetworkInterface], int]:
        query = self.db.query(
            NetworkInterface
        ).filter(
            NetworkInterface.company_id == company_id,
            NetworkInterface.device_id == device_id,
            NetworkInterface.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                NetworkInterface.status == status
            )

        if interface_type is not None:
            query = query.filter(
                NetworkInterface.interface_type
                == interface_type
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                NetworkInterface.name.ilike(
                    search_pattern
                )
            )

        total = query.count()

        sort_column = getattr(
            NetworkInterface,
            sort_by,
            NetworkInterface.created_at,
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_all_by_device(
        self,
        device_id: uuid.UUID,
    ) -> list[NetworkInterface]:
        return (
            self.db.query(NetworkInterface)
            .filter(
                NetworkInterface.device_id == device_id,
                NetworkInterface.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        interface: NetworkInterface,
        name: str | None = None,
        interface_type: str | None = None,
        status: str | None = None,
        mac_address: str | None = None,
        ip_address: str | None = None,
        speed_mbps: int | None = None,
        description: str | None = None,
    ) -> NetworkInterface:
        if name is not None:
            interface.name = name
        if interface_type is not None:
            interface.interface_type = interface_type
        if status is not None:
            interface.status = status
        if mac_address is not None:
            interface.mac_address = mac_address
        if ip_address is not None:
            interface.ip_address = ip_address
        if speed_mbps is not None:
            interface.speed_mbps = speed_mbps
        if description is not None:
            interface.description = description
        self.db.flush()
        return interface

    def soft_delete(
        self,
        interface: NetworkInterface,
    ) -> NetworkInterface:
        interface.deleted_at = datetime.utcnow()
        self.db.flush()
        return interface
