import math
import uuid

from sqlalchemy.orm import Session

from app.repositories.rack import RackRepository
from app.repositories.room import RoomRepository
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_STATUSES = {
    "ACTIVE",
    "FULL",
    "MAINTENANCE",
    "OFFLINE",
    "DECOMMISSIONED",
}

VALID_RACK_TYPES = {
    "SERVER_RACK",
    "NETWORK_RACK",
    "STORAGE_RACK",
    "OPEN_FRAME_RACK",
    "CUSTOM",
}

SORTABLE_FIELDS = {
    "name",
    "code",
    "rack_type",
    "status",
    "height_units",
    "position_in_room",
    "created_at",
    "updated_at",
}


class RackService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RackRepository(db)
        self.room_repo = RoomRepository(db)

    def _serialize(self, rack) -> dict:
        return {
            "id": str(rack.id),
            "company_id": str(rack.company_id),
            "room_id": str(rack.room_id),
            "name": rack.name,
            "code": rack.code,
            "rack_type": rack.rack_type,
            "status": rack.status,
            "height_units": rack.height_units,
            "width_mm": rack.width_mm,
            "depth_mm": rack.depth_mm,
            "max_weight_kg": rack.max_weight_kg,
            "current_weight_kg": rack.current_weight_kg,
            "power_capacity_kw": rack.power_capacity_kw,
            "current_power_usage_kw": (
                rack.current_power_usage_kw
            ),
            "cooling_capacity_kw": rack.cooling_capacity_kw,
            "manufacturer": rack.manufacturer,
            "model": rack.model,
            "serial_number": rack.serial_number,
            "position_in_room": rack.position_in_room,
            "description": rack.description,
            "created_at": rack.created_at.isoformat(),
            "updated_at": rack.updated_at.isoformat(),
        }

    def _validate_capacity(
        self,
        max_weight_kg: float | None = None,
        current_weight_kg: float | None = None,
        power_capacity_kw: float | None = None,
        current_power_usage_kw: float | None = None,
    ) -> None:
        if (
            max_weight_kg is not None
            and current_weight_kg is not None
            and current_weight_kg > max_weight_kg
        ):
            raise ValidationException(
                detail=(
                    "current_weight_kg cannot exceed "
                    "max_weight_kg"
                )
            )

        if (
            power_capacity_kw is not None
            and current_power_usage_kw is not None
            and current_power_usage_kw > power_capacity_kw
        ):
            raise ValidationException(
                detail=(
                    "current_power_usage_kw cannot "
                    "exceed power_capacity_kw"
                )
            )

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
    ) -> dict:
        if status not in VALID_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_STATUSES))}"
                )
            )

        if rack_type not in VALID_RACK_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid rack_type: {rack_type}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_RACK_TYPES))}"
                )
            )

        if not self.room_repo.get_active_by_company_and_id(
            company_id, room_id
        ):
            raise NotFoundException(
                detail="Room not found"
            )

        if self.repo.get_by_room_and_name(
            room_id, name
        ):
            raise DuplicateException(
                detail=(
                    "A rack with this name "
                    "already exists in this room"
                )
            )

        if self.repo.get_by_room_and_code(
            room_id, code
        ):
            raise DuplicateException(
                detail=(
                    "A rack with this code "
                    "already exists in this room"
                )
            )

        if serial_number:
            existing = self.repo.get_by_serial_number(
                serial_number
            )
            if existing:
                raise DuplicateException(
                    detail=(
                        "A rack with this serial number "
                        "already exists"
                    )
                )

        self._validate_capacity(
            max_weight_kg=max_weight_kg,
            current_weight_kg=current_weight_kg,
            power_capacity_kw=power_capacity_kw,
            current_power_usage_kw=current_power_usage_kw,
        )

        rack = self.repo.create(
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

        self.db.commit()
        self.db.refresh(rack)

        return self._serialize(rack)

    def get(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
    ) -> dict:
        rack = self.repo.get_active_by_company_and_id(
            company_id, rack_id
        )

        if not rack:
            raise NotFoundException(
                detail="Rack not found"
            )

        return self._serialize(rack)

    def get_capacity(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
    ) -> dict:
        rack = self.repo.get_active_by_company_and_id(
            company_id, rack_id
        )

        if not rack:
            raise NotFoundException(
                detail="Rack not found"
            )

        used_u = rack.height_units // 2
        available_u = rack.height_units - used_u

        used_power = (
            rack.current_power_usage_kw or 0
        )
        available_power = (
            (rack.power_capacity_kw - used_power)
            if rack.power_capacity_kw
            else None
        )

        used_weight = rack.current_weight_kg or 0
        available_weight = (
            (rack.max_weight_kg - used_weight)
            if rack.max_weight_kg
            else None
        )

        return {
            "total_u": rack.height_units,
            "used_u": used_u,
            "available_u": available_u,
            "power_capacity_kw": rack.power_capacity_kw,
            "used_power_kw": used_power,
            "available_power_kw": available_power,
            "weight_capacity_kg": rack.max_weight_kg,
            "used_weight_kg": used_weight,
            "available_weight_kg": available_weight,
        }

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

        if rack_type is not None:
            if rack_type not in VALID_RACK_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid rack_type filter: "
                        f"{rack_type}. Must be one of: "
                        f"{', '.join(sorted(VALID_RACK_TYPES))}"
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

        items, total = self.repo.list_by_room(
            company_id=company_id,
            room_id=room_id,
            status=status,
            rack_type=rack_type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "racks": [
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
        rack_id: uuid.UUID,
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
    ) -> dict:
        rack = self.repo.get_active_by_company_and_id(
            company_id, rack_id
        )

        if not rack:
            raise NotFoundException(
                detail="Rack not found"
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

        if rack_type is not None:
            if rack_type not in VALID_RACK_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid rack_type: {rack_type}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_RACK_TYPES))}"
                    )
                )

        if name is not None and name != rack.name:
            existing = (
                self.repo.get_by_room_and_name(
                    rack.room_id, name
                )
            )
            if existing and existing.id != rack.id:
                raise DuplicateException(
                    detail=(
                        "A rack with this name "
                        "already exists in this room"
                    )
                )

        if code is not None and code != rack.code:
            existing = (
                self.repo.get_by_room_and_code(
                    rack.room_id, code
                )
            )
            if existing and existing.id != rack.id:
                raise DuplicateException(
                    detail=(
                        "A rack with this code "
                        "already exists in this room"
                    )
                )

        if (
            serial_number is not None
            and serial_number != rack.serial_number
        ):
            if serial_number:
                existing = (
                    self.repo.get_by_serial_number(
                        serial_number
                    )
                )
                if existing and existing.id != rack.id:
                    raise DuplicateException(
                        detail=(
                            "A rack with this serial "
                            "number already exists"
                        )
                    )

        final_max_wt = (
            max_weight_kg
            if max_weight_kg is not None
            else rack.max_weight_kg
        )
        final_cur_wt = (
            current_weight_kg
            if current_weight_kg is not None
            else rack.current_weight_kg
        )
        final_pwr_cap = (
            power_capacity_kw
            if power_capacity_kw is not None
            else rack.power_capacity_kw
        )
        final_pwr_use = (
            current_power_usage_kw
            if current_power_usage_kw is not None
            else rack.current_power_usage_kw
        )
        self._validate_capacity(
            max_weight_kg=final_max_wt,
            current_weight_kg=final_cur_wt,
            power_capacity_kw=final_pwr_cap,
            current_power_usage_kw=final_pwr_use,
        )

        self.repo.update(
            rack,
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

        self.db.commit()
        self.db.refresh(rack)

        return self._serialize(rack)

    def delete(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
    ) -> dict:
        rack = self.repo.get_active_by_company_and_id(
            company_id, rack_id
        )

        if not rack:
            raise NotFoundException(
                detail="Rack not found"
            )

        self.repo.soft_delete(rack)
        self.db.commit()

        return {
            "message": (
                "Rack deleted successfully"
            )
        }
