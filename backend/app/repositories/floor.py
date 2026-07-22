import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.floor import Floor


class FloorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        building_id: uuid.UUID,
        name: str,
        code: str,
        floor_number: int,
        status: str = "PLANNED",
        description: str | None = None,
        total_area_sqm: float | None = None,
        max_power_capacity_kw: float | None = None,
        max_cooling_capacity_kw: float | None = None,
    ) -> Floor:
        floor = Floor(
            company_id=company_id,
            building_id=building_id,
            name=name,
            code=code,
            floor_number=floor_number,
            status=status,
            description=description,
            total_area_sqm=total_area_sqm,
            max_power_capacity_kw=max_power_capacity_kw,
            max_cooling_capacity_kw=(
                max_cooling_capacity_kw
            ),
        )
        self.db.add(floor)
        self.db.flush()
        return floor

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        floor_id: uuid.UUID,
    ) -> Floor | None:
        return (
            self.db.query(Floor)
            .filter(
                Floor.id == floor_id,
                Floor.company_id == company_id,
                Floor.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_building_and_name(
        self,
        building_id: uuid.UUID,
        name: str,
    ) -> Floor | None:
        return (
            self.db.query(Floor)
            .filter(
                Floor.building_id == building_id,
                Floor.name == name,
                Floor.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_building_and_code(
        self,
        building_id: uuid.UUID,
        code: str,
    ) -> Floor | None:
        return (
            self.db.query(Floor)
            .filter(
                Floor.building_id == building_id,
                Floor.code == code,
                Floor.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_building_and_floor_number(
        self,
        building_id: uuid.UUID,
        floor_number: int,
    ) -> Floor | None:
        return (
            self.db.query(Floor)
            .filter(
                Floor.building_id == building_id,
                Floor.floor_number == floor_number,
                Floor.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_building(
        self,
        company_id: uuid.UUID,
        building_id: uuid.UUID,
        status: str | None = None,
        floor_number: int | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Floor], int]:
        query = self.db.query(Floor).filter(
            Floor.company_id == company_id,
            Floor.building_id == building_id,
            Floor.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(Floor.status == status)

        if floor_number is not None:
            query = query.filter(
                Floor.floor_number == floor_number
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                Floor.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            Floor, sort_by, Floor.created_at
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
        floor: Floor,
        name: str | None = None,
        code: str | None = None,
        floor_number: int | None = None,
        status: str | None = None,
        description: str | None = None,
        total_area_sqm: float | None = None,
        max_power_capacity_kw: float | None = None,
        max_cooling_capacity_kw: float | None = None,
    ) -> Floor:
        if name is not None:
            floor.name = name
        if code is not None:
            floor.code = code
        if floor_number is not None:
            floor.floor_number = floor_number
        if status is not None:
            floor.status = status
        if description is not None:
            floor.description = description
        if total_area_sqm is not None:
            floor.total_area_sqm = total_area_sqm
        if max_power_capacity_kw is not None:
            floor.max_power_capacity_kw = (
                max_power_capacity_kw
            )
        if max_cooling_capacity_kw is not None:
            floor.max_cooling_capacity_kw = (
                max_cooling_capacity_kw
            )
        self.db.flush()
        return floor

    def soft_delete(self, floor: Floor) -> Floor:
        floor.deleted_at = datetime.utcnow()
        self.db.flush()
        return floor
