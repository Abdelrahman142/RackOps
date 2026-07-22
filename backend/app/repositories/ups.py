import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.ups import UPS


class UPSRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        capacity_kva: float,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str = "ACTIVE",
        battery_capacity_minutes: int | None = None,
        input_voltage: float | None = None,
        output_voltage: float | None = None,
        efficiency_percent: float | None = None,
    ) -> UPS:
        ups = UPS(
            company_id=company_id,
            room_id=room_id,
            name=name,
            capacity_kva=capacity_kva,
            model=model,
            manufacturer=manufacturer,
            serial_number=serial_number,
            status=status,
            battery_capacity_minutes=battery_capacity_minutes,
            input_voltage=input_voltage,
            output_voltage=output_voltage,
            efficiency_percent=efficiency_percent,
        )
        self.db.add(ups)
        self.db.flush()
        return ups

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        ups_id: uuid.UUID,
    ) -> UPS | None:
        return (
            self.db.query(UPS)
            .filter(
                UPS.id == ups_id,
                UPS.company_id == company_id,
                UPS.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_room_and_name(
        self,
        room_id: uuid.UUID,
        name: str,
    ) -> UPS | None:
        return (
            self.db.query(UPS)
            .filter(
                UPS.room_id == room_id,
                UPS.name == name,
                UPS.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_serial_number(
        self,
        serial_number: str,
    ) -> UPS | None:
        return (
            self.db.query(UPS)
            .filter(
                UPS.serial_number == serial_number,
                UPS.deleted_at.is_(None),
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
    ) -> tuple[list[UPS], int]:
        query = self.db.query(UPS).filter(
            UPS.company_id == company_id,
            UPS.room_id == room_id,
            UPS.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(UPS.status == status)

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                UPS.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            UPS, sort_by, UPS.created_at
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
    ) -> list[UPS]:
        return (
            self.db.query(UPS)
            .filter(
                UPS.room_id == room_id,
                UPS.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        ups: UPS,
        name: str | None = None,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str | None = None,
        capacity_kva: float | None = None,
        battery_capacity_minutes: int | None = None,
        input_voltage: float | None = None,
        output_voltage: float | None = None,
        efficiency_percent: float | None = None,
    ) -> UPS:
        if name is not None:
            ups.name = name
        if model is not None:
            ups.model = model
        if manufacturer is not None:
            ups.manufacturer = manufacturer
        if serial_number is not None:
            ups.serial_number = serial_number
        if status is not None:
            ups.status = status
        if capacity_kva is not None:
            ups.capacity_kva = capacity_kva
        if battery_capacity_minutes is not None:
            ups.battery_capacity_minutes = (
                battery_capacity_minutes
            )
        if input_voltage is not None:
            ups.input_voltage = input_voltage
        if output_voltage is not None:
            ups.output_voltage = output_voltage
        if efficiency_percent is not None:
            ups.efficiency_percent = efficiency_percent
        self.db.flush()
        return ups

    def soft_delete(self, ups: UPS) -> UPS:
        ups.deleted_at = datetime.utcnow()
        self.db.flush()
        return ups
