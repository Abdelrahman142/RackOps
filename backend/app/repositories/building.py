import math
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.building import Building


class BuildingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        name: str,
        code: str,
        address: str,
        status: str = "ACTIVE",
        description: str | None = None,
        number_of_floors: int = 1,
        total_area: float | None = None,
        power_capacity_kw: float | None = None,
        cooling_capacity_kw: float | None = None,
    ) -> Building:
        building = Building(
            company_id=company_id,
            datacenter_id=datacenter_id,
            name=name,
            code=code,
            address=address,
            status=status,
            description=description,
            number_of_floors=number_of_floors,
            total_area=total_area,
            power_capacity_kw=power_capacity_kw,
            cooling_capacity_kw=cooling_capacity_kw,
        )
        self.db.add(building)
        self.db.flush()
        return building

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        building_id: uuid.UUID,
    ) -> Building | None:
        return (
            self.db.query(Building)
            .filter(
                Building.id == building_id,
                Building.company_id == company_id,
                Building.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_datacenter_and_name(
        self,
        datacenter_id: uuid.UUID,
        name: str,
    ) -> Building | None:
        return (
            self.db.query(Building)
            .filter(
                Building.datacenter_id == datacenter_id,
                Building.name == name,
                Building.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_datacenter_and_code(
        self,
        datacenter_id: uuid.UUID,
        code: str,
    ) -> Building | None:
        return (
            self.db.query(Building)
            .filter(
                Building.datacenter_id == datacenter_id,
                Building.code == code,
                Building.deleted_at.is_(None),
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
    ) -> tuple[list[Building], int]:
        query = self.db.query(Building).filter(
            Building.company_id == company_id,
            Building.datacenter_id == datacenter_id,
            Building.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(Building.status == status)

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                Building.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            Building, sort_by, Building.created_at
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
        building: Building,
        name: str | None = None,
        code: str | None = None,
        address: str | None = None,
        status: str | None = None,
        description: str | None = None,
        number_of_floors: int | None = None,
        total_area: float | None = None,
        power_capacity_kw: float | None = None,
        cooling_capacity_kw: float | None = None,
    ) -> Building:
        if name is not None:
            building.name = name
        if code is not None:
            building.code = code
        if address is not None:
            building.address = address
        if status is not None:
            building.status = status
        if description is not None:
            building.description = description
        if number_of_floors is not None:
            building.number_of_floors = number_of_floors
        if total_area is not None:
            building.total_area = total_area
        if power_capacity_kw is not None:
            building.power_capacity_kw = power_capacity_kw
        if cooling_capacity_kw is not None:
            building.cooling_capacity_kw = (
                cooling_capacity_kw
            )
        self.db.flush()
        return building

    def soft_delete(
        self, building: Building
    ) -> Building:
        building.deleted_at = datetime.utcnow()
        self.db.flush()
        return building
