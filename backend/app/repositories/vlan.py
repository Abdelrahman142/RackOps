import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.vlan import VLAN


class VLANRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        name: str,
        vlan_id: int,
        description: str | None = None,
        status: str = "ACTIVE",
    ) -> VLAN:
        vlan = VLAN(
            company_id=company_id,
            datacenter_id=datacenter_id,
            name=name,
            vlan_id=vlan_id,
            description=description,
            status=status,
        )
        self.db.add(vlan)
        self.db.flush()
        return vlan

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        vlan_id: uuid.UUID,
    ) -> VLAN | None:
        return (
            self.db.query(VLAN)
            .filter(
                VLAN.id == vlan_id,
                VLAN.company_id == company_id,
                VLAN.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_company_and_vlan_id(
        self,
        company_id: uuid.UUID,
        vlan_id: int,
    ) -> VLAN | None:
        return (
            self.db.query(VLAN)
            .filter(
                VLAN.company_id == company_id,
                VLAN.vlan_id == vlan_id,
                VLAN.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_datacenter_and_name(
        self,
        datacenter_id: uuid.UUID,
        name: str,
    ) -> VLAN | None:
        return (
            self.db.query(VLAN)
            .filter(
                VLAN.datacenter_id == datacenter_id,
                VLAN.name == name,
                VLAN.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_datacenter(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[VLAN], int]:
        query = self.db.query(VLAN).filter(
            VLAN.company_id == company_id,
            VLAN.datacenter_id == datacenter_id,
            VLAN.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                VLAN.status == status
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                VLAN.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            VLAN, sort_by, VLAN.created_at
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
        vlan: VLAN,
        name: str | None = None,
        vlan_id: int | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> VLAN:
        if name is not None:
            vlan.name = name
        if vlan_id is not None:
            vlan.vlan_id = vlan_id
        if description is not None:
            vlan.description = description
        if status is not None:
            vlan.status = status
        self.db.flush()
        return vlan

    def soft_delete(self, vlan: VLAN) -> VLAN:
        vlan.deleted_at = datetime.utcnow()
        self.db.flush()
        return vlan
