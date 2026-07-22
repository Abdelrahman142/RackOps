import math
import uuid

from sqlalchemy.orm import Session

from app.repositories.floor import FloorRepository
from app.repositories.room import RoomRepository
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_STATUSES = {
    "ACTIVE",
    "MAINTENANCE",
    "OFFLINE",
    "PLANNED",
}

VALID_ROOM_TYPES = {
    "SERVER_ROOM",
    "NETWORK_ROOM",
    "STORAGE_ROOM",
    "UPS_ROOM",
    "CONTROL_ROOM",
    "OTHER",
}

SORTABLE_FIELDS = {
    "name",
    "code",
    "room_type",
    "status",
    "created_at",
    "updated_at",
}


class RoomService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RoomRepository(db)
        self.floor_repo = FloorRepository(db)

    def _serialize(self, room) -> dict:
        return {
            "id": str(room.id),
            "company_id": str(room.company_id),
            "floor_id": str(room.floor_id),
            "name": room.name,
            "code": room.code,
            "room_type": room.room_type,
            "description": room.description,
            "status": room.status,
            "area_sqm": room.area_sqm,
            "height_meters": room.height_meters,
            "max_rack_capacity": room.max_rack_capacity,
            "max_power_capacity_kw": (
                room.max_power_capacity_kw
            ),
            "max_cooling_capacity_kw": (
                room.max_cooling_capacity_kw
            ),
            "temperature_min": room.temperature_min,
            "temperature_max": room.temperature_max,
            "humidity_min": room.humidity_min,
            "humidity_max": room.humidity_max,
            "created_at": room.created_at.isoformat(),
            "updated_at": room.updated_at.isoformat(),
        }

    def _validate_ranges(
        self,
        temperature_min: float | None = None,
        temperature_max: float | None = None,
        humidity_min: float | None = None,
        humidity_max: float | None = None,
    ) -> None:
        if (
            temperature_min is not None
            and temperature_max is not None
            and temperature_min > temperature_max
        ):
            raise ValidationException(
                detail=(
                    "temperature_min must not be "
                    "greater than temperature_max"
                )
            )

        if (
            humidity_min is not None
            and humidity_max is not None
            and humidity_min > humidity_max
        ):
            raise ValidationException(
                detail=(
                    "humidity_min must not be "
                    "greater than humidity_max"
                )
            )

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
    ) -> dict:
        if status not in VALID_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_STATUSES))}"
                )
            )

        if room_type not in VALID_ROOM_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid room_type: {room_type}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_ROOM_TYPES))}"
                )
            )

        if not self.floor_repo.get_active_by_company_and_id(
            company_id, floor_id
        ):
            raise NotFoundException(
                detail="Floor not found"
            )

        if self.repo.get_by_floor_and_name(
            floor_id, name
        ):
            raise DuplicateException(
                detail=(
                    "A room with this name "
                    "already exists on this floor"
                )
            )

        if self.repo.get_by_floor_and_code(
            floor_id, code
        ):
            raise DuplicateException(
                detail=(
                    "A room with this code "
                    "already exists on this floor"
                )
            )

        self._validate_ranges(
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            humidity_min=humidity_min,
            humidity_max=humidity_max,
        )

        room = self.repo.create(
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

        self.db.commit()
        self.db.refresh(room)

        return self._serialize(room)

    def get(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
    ) -> dict:
        room = self.repo.get_active_by_company_and_id(
            company_id, room_id
        )

        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        return self._serialize(room)

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
    ) -> dict:
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_STATUSES))}"
                    )
                )

        if room_type is not None:
            if room_type not in VALID_ROOM_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid room_type filter: "
                        f"{room_type}. Must be one of: "
                        f"{', '.join(sorted(VALID_ROOM_TYPES))}"
                    )
                )

        if sort_by not in SORTABLE_FIELDS:
            raise ValidationException(
                detail=(
                    f"Invalid sort field: {sort_by}. "
                    "Must be one of: "
                    f"{', '.join(sorted(SORTABLE_FIELDS))}"
                )
            )

        if sort_order not in ("asc", "desc"):
            raise ValidationException(
                detail=(
                    "Invalid sort order. "
                    "Must be 'asc' or 'desc'"
                )
            )

        if page < 1:
            page = 1
        if size < 1:
            size = 1
        if size > 100:
            size = 100

        items, total = self.repo.list_by_floor(
            company_id=company_id,
            floor_id=floor_id,
            status=status,
            room_type=room_type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "rooms": [
                self._serialize(r) for r in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
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
    ) -> dict:
        room = self.repo.get_active_by_company_and_id(
            company_id, room_id
        )

        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        if status is not None:
            if status not in VALID_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_STATUSES))}"
                    )
                )

        if room_type is not None:
            if room_type not in VALID_ROOM_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid room_type: {room_type}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_ROOM_TYPES))}"
                    )
                )

        if name is not None and name != room.name:
            existing = (
                self.repo.get_by_floor_and_name(
                    room.floor_id, name
                )
            )
            if existing and existing.id != room.id:
                raise DuplicateException(
                    detail=(
                        "A room with this name "
                        "already exists on this floor"
                    )
                )

        if code is not None and code != room.code:
            existing = (
                self.repo.get_by_floor_and_code(
                    room.floor_id, code
                )
            )
            if existing and existing.id != room.id:
                raise DuplicateException(
                    detail=(
                        "A room with this code "
                        "already exists on this floor"
                    )
                )

        final_t_min = (
            temperature_min
            if temperature_min is not None
            else room.temperature_min
        )
        final_t_max = (
            temperature_max
            if temperature_max is not None
            else room.temperature_max
        )
        final_h_min = (
            humidity_min
            if humidity_min is not None
            else room.humidity_min
        )
        final_h_max = (
            humidity_max
            if humidity_max is not None
            else room.humidity_max
        )
        self._validate_ranges(
            temperature_min=final_t_min,
            temperature_max=final_t_max,
            humidity_min=final_h_min,
            humidity_max=final_h_max,
        )

        self.repo.update(
            room,
            name=name,
            code=code,
            room_type=room_type,
            status=status,
            description=description,
            area_sqm=area_sqm,
            height_meters=height_meters,
            max_rack_capacity=max_rack_capacity,
            max_power_capacity_kw=max_power_capacity_kw,
            max_cooling_capacity_kw=max_cooling_capacity_kw,
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            humidity_min=humidity_min,
            humidity_max=humidity_max,
        )

        self.db.commit()
        self.db.refresh(room)

        return self._serialize(room)

    def delete(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
    ) -> dict:
        room = self.repo.get_active_by_company_and_id(
            company_id, room_id
        )

        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        self.repo.soft_delete(room)
        self.db.commit()

        return {
            "message": (
                "Room deleted successfully"
            )
        }
