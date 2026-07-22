import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.environmental_zone import (
    EnvironmentalZone,
)


class EnvironmentalZoneRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        description: str | None = None,
        target_temperature_min: float | None = None,
        target_temperature_max: float | None = None,
        target_humidity_min: float | None = None,
        target_humidity_max: float | None = None,
        status: str = "ACTIVE",
    ) -> EnvironmentalZone:
        zone = EnvironmentalZone(
            company_id=company_id,
            room_id=room_id,
            name=name,
            description=description,
            target_temperature_min=target_temperature_min,
            target_temperature_max=target_temperature_max,
            target_humidity_min=target_humidity_min,
            target_humidity_max=target_humidity_max,
            status=status,
        )
        self.db.add(zone)
        self.db.flush()
        return zone

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        zone_id: uuid.UUID,
    ) -> EnvironmentalZone | None:
        return (
            self.db.query(EnvironmentalZone)
            .filter(
                EnvironmentalZone.id == zone_id,
                EnvironmentalZone.company_id == company_id,
                EnvironmentalZone.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_room_and_name(
        self,
        room_id: uuid.UUID,
        name: str,
    ) -> EnvironmentalZone | None:
        return (
            self.db.query(EnvironmentalZone)
            .filter(
                EnvironmentalZone.room_id == room_id,
                EnvironmentalZone.name == name,
                EnvironmentalZone.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_room(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[EnvironmentalZone], int]:
        query = self.db.query(EnvironmentalZone).filter(
            EnvironmentalZone.company_id == company_id,
            EnvironmentalZone.room_id == room_id,
            EnvironmentalZone.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                EnvironmentalZone.status == status
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                EnvironmentalZone.name.ilike(
                    search_pattern
                )
            )

        total = query.count()

        sort_column = getattr(
            EnvironmentalZone,
            sort_by,
            EnvironmentalZone.created_at,
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_all_by_room(
        self,
        room_id: uuid.UUID,
    ) -> list[EnvironmentalZone]:
        return (
            self.db.query(EnvironmentalZone)
            .filter(
                EnvironmentalZone.room_id == room_id,
                EnvironmentalZone.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        zone: EnvironmentalZone,
        name: str | None = None,
        description: str | None = None,
        target_temperature_min: float | None = None,
        target_temperature_max: float | None = None,
        target_humidity_min: float | None = None,
        target_humidity_max: float | None = None,
        status: str | None = None,
    ) -> EnvironmentalZone:
        if name is not None:
            zone.name = name
        if description is not None:
            zone.description = description
        if target_temperature_min is not None:
            zone.target_temperature_min = (
                target_temperature_min
            )
        if target_temperature_max is not None:
            zone.target_temperature_max = (
                target_temperature_max
            )
        if target_humidity_min is not None:
            zone.target_humidity_min = target_humidity_min
        if target_humidity_max is not None:
            zone.target_humidity_max = target_humidity_max
        if status is not None:
            zone.status = status
        self.db.flush()
        return zone

    def soft_delete(
        self, zone: EnvironmentalZone
    ) -> EnvironmentalZone:
        zone.deleted_at = datetime.utcnow()
        self.db.flush()
        return zone
