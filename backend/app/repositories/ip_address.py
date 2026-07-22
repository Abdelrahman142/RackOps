import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.ip_address import IPAddress


class IPAddressRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
        address: str,
        device_interface_id: uuid.UUID | None = None,
        status: str = "AVAILABLE",
        description: str | None = None,
    ) -> IPAddress:
        ip = IPAddress(
            company_id=company_id,
            subnet_id=subnet_id,
            address=address,
            device_interface_id=device_interface_id,
            status=status,
            description=description,
        )
        self.db.add(ip)
        self.db.flush()
        return ip

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        ip_id: uuid.UUID,
    ) -> IPAddress | None:
        return (
            self.db.query(IPAddress)
            .filter(
                IPAddress.id == ip_id,
                IPAddress.company_id == company_id,
                IPAddress.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_company_and_address(
        self,
        company_id: uuid.UUID,
        address: str,
    ) -> IPAddress | None:
        return (
            self.db.query(IPAddress)
            .filter(
                IPAddress.company_id == company_id,
                IPAddress.address == address,
                IPAddress.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_subnet(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[IPAddress], int]:
        query = self.db.query(IPAddress).filter(
            IPAddress.company_id == company_id,
            IPAddress.subnet_id == subnet_id,
            IPAddress.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                IPAddress.status == status
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                IPAddress.address.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            IPAddress, sort_by, IPAddress.created_at
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def update(
        self,
        ip: IPAddress,
        device_interface_id: uuid.UUID | None = None,
        address: str | None = None,
        status: str | None = None,
        description: str | None = None,
    ) -> IPAddress:
        if device_interface_id is not None:
            ip.device_interface_id = device_interface_id
        if address is not None:
            ip.address = address
        if status is not None:
            ip.status = status
        if description is not None:
            ip.description = description
        self.db.flush()
        return ip

    def soft_delete(self, ip: IPAddress) -> IPAddress:
        ip.deleted_at = datetime.utcnow()
        self.db.flush()
        return ip
