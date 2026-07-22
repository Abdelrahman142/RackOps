import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.rack import Rack


class RackRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        code: str,
        rack_type: str = "SERVER_RACK",
        status: str = "ACTIVE",
        height_units: int = 42,
        width_mm: float | None = None,
        depth_mm: float | None = None,
        max_weight_kg: float | None = None,
        current_weight_kg: float | None = 0,
        power_capacity_kw: float | None = None,
        current_power_usage_kw: float | None = 0,
        cooling_capacity_kw: float | None = None,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        position_in_room: int | None = None,
        description: str | None = None,
    ) -> Rack:
        rack = Rack(
            company_id=company_id,
            room_id=room_id,
            name=name,
            code=code,
            rack_type=rack_type,
            status=status,
            height_units=height_units,
            width_mm=width_mm,
            depth_mm=depth_mm,
            max_weight_kg=max_weight_kg,
            current_weight_kg=current_weight_kg,
            power_capacity_kw=power_capacity_kw,
            current_power_usage_kw=current_power_usage_kw,
            cooling_capacity_kw=cooling_capacity_kw,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            position_in_room=position_in_room,
            description=description,
        )
        self.db.add(rack)
        self.db.flush()
        return rack

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
    ) -> Rack | None:
        return (
            self.db.query(Rack)
            .filter(
                Rack.id == rack_id,
                Rack.company_id == company_id,
                Rack.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_room_and_name(
        self,
        room_id: uuid.UUID,
        name: str,
    ) -> Rack | None:
        return (
            self.db.query(Rack)
            .filter(
                Rack.room_id == room_id,
                Rack.name == name,
                Rack.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_room_and_code(
        self,
        room_id: uuid.UUID,
        code: str,
    ) -> Rack | None:
        return (
            self.db.query(Rack)
            .filter(
                Rack.room_id == room_id,
                Rack.code == code,
                Rack.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_serial_number(
        self,
        serial_number: str,
    ) -> Rack | None:
        return (
            self.db.query(Rack)
            .filter(
                Rack.serial_number == serial_number,
                Rack.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_room(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        status: str | None = None,
        rack_type: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Rack], int]:
        query = self.db.query(Rack).filter(
            Rack.company_id == company_id,
            Rack.room_id == room_id,
            Rack.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(Rack.status == status)

        if rack_type is not None:
            query = query.filter(
                Rack.rack_type == rack_type
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                Rack.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            Rack, sort_by, Rack.created_at
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
        rack: Rack,
        name: str | None = None,
        code: str | None = None,
        rack_type: str | None = None,
        status: str | None = None,
        height_units: int | None = None,
        width_mm: float | None = None,
        depth_mm: float | None = None,
        max_weight_kg: float | None = None,
        current_weight_kg: float | None = None,
        power_capacity_kw: float | None = None,
        current_power_usage_kw: float | None = None,
        cooling_capacity_kw: float | None = None,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        position_in_room: int | None = None,
        description: str | None = None,
    ) -> Rack:
        if name is not None:
            rack.name = name
        if code is not None:
            rack.code = code
        if rack_type is not None:
            rack.rack_type = rack_type
        if status is not None:
            rack.status = status
        if height_units is not None:
            rack.height_units = height_units
        if width_mm is not None:
            rack.width_mm = width_mm
        if depth_mm is not None:
            rack.depth_mm = depth_mm
        if max_weight_kg is not None:
            rack.max_weight_kg = max_weight_kg
        if current_weight_kg is not None:
            rack.current_weight_kg = current_weight_kg
        if power_capacity_kw is not None:
            rack.power_capacity_kw = power_capacity_kw
        if current_power_usage_kw is not None:
            rack.current_power_usage_kw = (
                current_power_usage_kw
            )
        if cooling_capacity_kw is not None:
            rack.cooling_capacity_kw = cooling_capacity_kw
        if manufacturer is not None:
            rack.manufacturer = manufacturer
        if model is not None:
            rack.model = model
        if serial_number is not None:
            rack.serial_number = serial_number
        if position_in_room is not None:
            rack.position_in_room = position_in_room
        if description is not None:
            rack.description = description
        self.db.flush()
        return rack

    def soft_delete(self, rack: Rack) -> Rack:
        rack.deleted_at = datetime.utcnow()
        self.db.flush()
        return rack
