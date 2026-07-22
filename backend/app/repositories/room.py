import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.room import Room


class RoomRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        floor_id: uuid.UUID,
        name: str,
        code: str,
        room_type: str = "SERVER_ROOM",
        status: str = "PLANNED",
        description: str | None = None,
        area_sqm: float | None = None,
        height_meters: float | None = None,
        max_rack_capacity: int | None = None,
        max_power_capacity_kw: float | None = None,
        max_cooling_capacity_kw: float | None = None,
        temperature_min: float | None = None,
        temperature_max: float | None = None,
        humidity_min: float | None = None,
        humidity_max: float | None = None,
    ) -> Room:
        room = Room(
            company_id=company_id,
            floor_id=floor_id,
            name=name,
            code=code,
            room_type=room_type,
            status=status,
            description=description,
            area_sqm=area_sqm,
            height_meters=height_meters,
            max_rack_capacity=max_rack_capacity,
            max_power_capacity_kw=max_power_capacity_kw,
            max_cooling_capacity_kw=(
                max_cooling_capacity_kw
            ),
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            humidity_min=humidity_min,
            humidity_max=humidity_max,
        )
        self.db.add(room)
        self.db.flush()
        return room

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
    ) -> Room | None:
        return (
            self.db.query(Room)
            .filter(
                Room.id == room_id,
                Room.company_id == company_id,
                Room.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_floor_and_name(
        self,
        floor_id: uuid.UUID,
        name: str,
    ) -> Room | None:
        return (
            self.db.query(Room)
            .filter(
                Room.floor_id == floor_id,
                Room.name == name,
                Room.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_floor_and_code(
        self,
        floor_id: uuid.UUID,
        code: str,
    ) -> Room | None:
        return (
            self.db.query(Room)
            .filter(
                Room.floor_id == floor_id,
                Room.code == code,
                Room.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_floor(
        self,
        company_id: uuid.UUID,
        floor_id: uuid.UUID,
        status: str | None = None,
        room_type: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Room], int]:
        query = self.db.query(Room).filter(
            Room.company_id == company_id,
            Room.floor_id == floor_id,
            Room.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(Room.status == status)

        if room_type is not None:
            query = query.filter(
                Room.room_type == room_type
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                Room.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            Room, sort_by, Room.created_at
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
        room: Room,
        name: str | None = None,
        code: str | None = None,
        room_type: str | None = None,
        status: str | None = None,
        description: str | None = None,
        area_sqm: float | None = None,
        height_meters: float | None = None,
        max_rack_capacity: int | None = None,
        max_power_capacity_kw: float | None = None,
        max_cooling_capacity_kw: float | None = None,
        temperature_min: float | None = None,
        temperature_max: float | None = None,
        humidity_min: float | None = None,
        humidity_max: float | None = None,
    ) -> Room:
        if name is not None:
            room.name = name
        if code is not None:
            room.code = code
        if room_type is not None:
            room.room_type = room_type
        if status is not None:
            room.status = status
        if description is not None:
            room.description = description
        if area_sqm is not None:
            room.area_sqm = area_sqm
        if height_meters is not None:
            room.height_meters = height_meters
        if max_rack_capacity is not None:
            room.max_rack_capacity = max_rack_capacity
        if max_power_capacity_kw is not None:
            room.max_power_capacity_kw = (
                max_power_capacity_kw
            )
        if max_cooling_capacity_kw is not None:
            room.max_cooling_capacity_kw = (
                max_cooling_capacity_kw
            )
        if temperature_min is not None:
            room.temperature_min = temperature_min
        if temperature_max is not None:
            room.temperature_max = temperature_max
        if humidity_min is not None:
            room.humidity_min = humidity_min
        if humidity_max is not None:
            room.humidity_max = humidity_max
        self.db.flush()
        return room

    def soft_delete(self, room: Room) -> Room:
        room.deleted_at = datetime.utcnow()
        self.db.flush()
        return room
