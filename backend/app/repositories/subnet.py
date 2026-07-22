import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.subnet import Subnet


class SubnetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        vlan_id: uuid.UUID,
        network_address: str,
        cidr: int,
        gateway: str | None = None,
        description: str | None = None,
    ) -> Subnet:
        subnet = Subnet(
            company_id=company_id,
            vlan_id=vlan_id,
            network_address=network_address,
            cidr=cidr,
            gateway=gateway,
            description=description,
        )
        self.db.add(subnet)
        self.db.flush()
        return subnet

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        subnet_id: uuid.UUID,
    ) -> Subnet | None:
        return (
            self.db.query(Subnet)
            .filter(
                Subnet.id == subnet_id,
                Subnet.company_id == company_id,
                Subnet.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_company_and_network(
        self,
        company_id: uuid.UUID,
        network_address: str,
        cidr: int,
    ) -> Subnet | None:
        return (
            self.db.query(Subnet)
            .filter(
                Subnet.company_id == company_id,
                Subnet.network_address == network_address,
                Subnet.cidr == cidr,
                Subnet.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_vlan(
        self,
        company_id: uuid.UUID,
        vlan_id: uuid.UUID,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Subnet], int]:
        query = self.db.query(Subnet).filter(
            Subnet.company_id == company_id,
            Subnet.vlan_id == vlan_id,
            Subnet.deleted_at.is_(None),
        )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                Subnet.network_address.ilike(
                    search_pattern
                )
            )

        total = query.count()

        sort_column = getattr(
            Subnet, sort_by, Subnet.created_at
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
        subnet: Subnet,
        network_address: str | None = None,
        cidr: int | None = None,
        gateway: str | None = None,
        description: str | None = None,
    ) -> Subnet:
        if network_address is not None:
            subnet.network_address = network_address
        if cidr is not None:
            subnet.cidr = cidr
        if gateway is not None:
            subnet.gateway = gateway
        if description is not None:
            subnet.description = description
        self.db.flush()
        return subnet

    def soft_delete(self, subnet: Subnet) -> Subnet:
        subnet.deleted_at = datetime.utcnow()
        self.db.flush()
        return subnet
