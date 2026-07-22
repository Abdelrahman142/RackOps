import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.sensor import Sensor


class SensorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        zone_id: uuid.UUID,
        name: str,
        sensor_type: str,
        status: str = "ACTIVE",
        location_description: str | None = None,
    ) -> Sensor:
        sensor = Sensor(
            company_id=company_id,
            zone_id=zone_id,
            name=name,
            sensor_type=sensor_type,
            status=status,
            location_description=location_description,
        )
        self.db.add(sensor)
        self.db.flush()
        return sensor

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        sensor_id: uuid.UUID,
    ) -> Sensor | None:
        return (
            self.db.query(Sensor)
            .filter(
                Sensor.id == sensor_id,
                Sensor.company_id == company_id,
                Sensor.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_zone_and_name(
        self,
        zone_id: uuid.UUID,
        name: str,
    ) -> Sensor | None:
        return (
            self.db.query(Sensor)
            .filter(
                Sensor.zone_id == zone_id,
                Sensor.name == name,
                Sensor.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_zone(
        self,
        company_id: uuid.UUID,
        zone_id: uuid.UUID,
        status: str | None = None,
        sensor_type: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Sensor], int]:
        query = self.db.query(Sensor).filter(
            Sensor.company_id == company_id,
            Sensor.zone_id == zone_id,
            Sensor.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                Sensor.status == status
            )

        if sensor_type is not None:
            query = query.filter(
                Sensor.sensor_type == sensor_type
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                Sensor.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            Sensor, sort_by, Sensor.created_at
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_all_by_zone(
        self,
        zone_id: uuid.UUID,
    ) -> list[Sensor]:
        return (
            self.db.query(Sensor)
            .filter(
                Sensor.zone_id == zone_id,
                Sensor.deleted_at.is_(None),
            )
            .all()
        )

    def list_by_type_in_zones(
        self,
        zone_ids: list[uuid.UUID],
        sensor_type: str,
    ) -> list[Sensor]:
        if not zone_ids:
            return []
        return (
            self.db.query(Sensor)
            .filter(
                Sensor.zone_id.in_(zone_ids),
                Sensor.sensor_type == sensor_type,
                Sensor.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        sensor: Sensor,
        name: str | None = None,
        sensor_type: str | None = None,
        status: str | None = None,
        location_description: str | None = None,
        last_value: float | None = None,
        last_unit: str | None = None,
        last_reading_at: datetime | None = None,
    ) -> Sensor:
        if name is not None:
            sensor.name = name
        if sensor_type is not None:
            sensor.sensor_type = sensor_type
        if status is not None:
            sensor.status = status
        if location_description is not None:
            sensor.location_description = (
                location_description
            )
        if last_value is not None:
            sensor.last_value = last_value
        if last_unit is not None:
            sensor.last_unit = last_unit
        if last_reading_at is not None:
            sensor.last_reading_at = last_reading_at
        self.db.flush()
        return sensor

    def soft_delete(self, sensor: Sensor) -> Sensor:
        sensor.deleted_at = datetime.utcnow()
        self.db.flush()
        return sensor
