import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.cooling_unit import CoolingUnit


class CoolingUnitRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        cooling_capacity_kw: float,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        type: str = "CRAC",
        status: str = "ACTIVE",
        airflow_cfm: float | None = None,
        power_consumption_kw: float | None = None,
    ) -> CoolingUnit:
        unit = CoolingUnit(
            company_id=company_id,
            room_id=room_id,
            name=name,
            cooling_capacity_kw=cooling_capacity_kw,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            type=type,
            status=status,
            airflow_cfm=airflow_cfm,
            power_consumption_kw=power_consumption_kw,
        )
        self.db.add(unit)
        self.db.flush()
        return unit

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        unit_id: uuid.UUID,
    ) -> CoolingUnit | None:
        return (
            self.db.query(CoolingUnit)
            .filter(
                CoolingUnit.id == unit_id,
                CoolingUnit.company_id == company_id,
                CoolingUnit.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_room_and_name(
        self,
        room_id: uuid.UUID,
        name: str,
    ) -> CoolingUnit | None:
        return (
            self.db.query(CoolingUnit)
            .filter(
                CoolingUnit.room_id == room_id,
                CoolingUnit.name == name,
                CoolingUnit.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_serial_number(
        self,
        serial_number: str,
    ) -> CoolingUnit | None:
        return (
            self.db.query(CoolingUnit)
            .filter(
                CoolingUnit.serial_number == serial_number,
                CoolingUnit.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_room(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        status: str | None = None,
        type: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[CoolingUnit], int]:
        query = self.db.query(CoolingUnit).filter(
            CoolingUnit.company_id == company_id,
            CoolingUnit.room_id == room_id,
            CoolingUnit.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                CoolingUnit.status == status
            )

        if type is not None:
            query = query.filter(
                CoolingUnit.type == type
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                CoolingUnit.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            CoolingUnit, sort_by, CoolingUnit.created_at
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
    ) -> list[CoolingUnit]:
        return (
            self.db.query(CoolingUnit)
            .filter(
                CoolingUnit.room_id == room_id,
                CoolingUnit.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        unit: CoolingUnit,
        name: str | None = None,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        type: str | None = None,
        status: str | None = None,
        cooling_capacity_kw: float | None = None,
        airflow_cfm: float | None = None,
        power_consumption_kw: float | None = None,
    ) -> CoolingUnit:
        if name is not None:
            unit.name = name
        if manufacturer is not None:
            unit.manufacturer = manufacturer
        if model is not None:
            unit.model = model
        if serial_number is not None:
            unit.serial_number = serial_number
        if type is not None:
            unit.type = type
        if status is not None:
            unit.status = status
        if cooling_capacity_kw is not None:
            unit.cooling_capacity_kw = cooling_capacity_kw
        if airflow_cfm is not None:
            unit.airflow_cfm = airflow_cfm
        if power_consumption_kw is not None:
            unit.power_consumption_kw = power_consumption_kw
        self.db.flush()
        return unit

    def soft_delete(self, unit: CoolingUnit) -> CoolingUnit:
        unit.deleted_at = datetime.utcnow()
        self.db.flush()
        return unit
