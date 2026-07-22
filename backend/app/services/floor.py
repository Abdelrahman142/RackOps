import math
import uuid

from sqlalchemy.orm import Session

from app.repositories.building import BuildingRepository
from app.repositories.floor import FloorRepository
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

SORTABLE_FIELDS = {
    "name",
    "code",
    "floor_number",
    "status",
    "created_at",
    "updated_at",
}


class FloorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FloorRepository(db)
        self.building_repo = BuildingRepository(db)

    def _serialize(self, floor) -> dict:
        return {
            "id": str(floor.id),
            "company_id": str(floor.company_id),
            "building_id": str(floor.building_id),
            "name": floor.name,
            "code": floor.code,
            "floor_number": floor.floor_number,
            "description": floor.description,
            "status": floor.status,
            "total_area_sqm": floor.total_area_sqm,
            "max_power_capacity_kw": (
                floor.max_power_capacity_kw
            ),
            "max_cooling_capacity_kw": (
                floor.max_cooling_capacity_kw
            ),
            "created_at": floor.created_at.isoformat(),
            "updated_at": floor.updated_at.isoformat(),
        }

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
    ) -> dict:
        if status not in VALID_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_STATUSES))}"
                )
            )

        if not self.building_repo.get_active_by_company_and_id(
            company_id, building_id
        ):
            raise NotFoundException(
                detail="Building not found"
            )

        if self.repo.get_by_building_and_name(
            building_id, name
        ):
            raise DuplicateException(
                detail=(
                    "A floor with this name "
                    "already exists in this building"
                )
            )

        if self.repo.get_by_building_and_code(
            building_id, code
        ):
            raise DuplicateException(
                detail=(
                    "A floor with this code "
                    "already exists in this building"
                )
            )

        if self.repo.get_by_building_and_floor_number(
            building_id, floor_number
        ):
            raise DuplicateException(
                detail=(
                    "A floor with this floor number "
                    "already exists in this building"
                )
            )

        floor = self.repo.create(
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

        self.db.commit()
        self.db.refresh(floor)

        return self._serialize(floor)

    def get(
        self,
        company_id: uuid.UUID,
        floor_id: uuid.UUID,
    ) -> dict:
        floor = self.repo.get_active_by_company_and_id(
            company_id, floor_id
        )

        if not floor:
            raise NotFoundException(
                detail="Floor not found"
            )

        return self._serialize(floor)

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

        items, total = self.repo.list_by_building(
            company_id=company_id,
            building_id=building_id,
            status=status,
            floor_number=floor_number,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "floors": [
                self._serialize(f) for f in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update(
        self,
        company_id: uuid.UUID,
        floor_id: uuid.UUID,
        name: str | None = None,
        code: str | None = None,
        floor_number: int | None = None,
        status: str | None = None,
        description: str | None = None,
        total_area_sqm: float | None = None,
        max_power_capacity_kw: float | None = None,
        max_cooling_capacity_kw: float | None = None,
    ) -> dict:
        floor = self.repo.get_active_by_company_and_id(
            company_id, floor_id
        )

        if not floor:
            raise NotFoundException(
                detail="Floor not found"
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

        if name is not None and name != floor.name:
            existing = (
                self.repo.get_by_building_and_name(
                    floor.building_id, name
                )
            )
            if existing and existing.id != floor.id:
                raise DuplicateException(
                    detail=(
                        "A floor with this name "
                        "already exists in this building"
                    )
                )

        if code is not None and code != floor.code:
            existing = (
                self.repo.get_by_building_and_code(
                    floor.building_id, code
                )
            )
            if existing and existing.id != floor.id:
                raise DuplicateException(
                    detail=(
                        "A floor with this code "
                        "already exists in this building"
                    )
                )

        if (
            floor_number is not None
            and floor_number != floor.floor_number
        ):
            existing = (
                self.repo.get_by_building_and_floor_number(
                    floor.building_id, floor_number
                )
            )
            if existing and existing.id != floor.id:
                raise DuplicateException(
                    detail=(
                        "A floor with this floor number "
                        "already exists in this building"
                    )
                )

        self.repo.update(
            floor,
            name=name,
            code=code,
            floor_number=floor_number,
            status=status,
            description=description,
            total_area_sqm=total_area_sqm,
            max_power_capacity_kw=max_power_capacity_kw,
            max_cooling_capacity_kw=max_cooling_capacity_kw,
        )

        self.db.commit()
        self.db.refresh(floor)

        return self._serialize(floor)

    def delete(
        self,
        company_id: uuid.UUID,
        floor_id: uuid.UUID,
    ) -> dict:
        floor = self.repo.get_active_by_company_and_id(
            company_id, floor_id
        )

        if not floor:
            raise NotFoundException(
                detail="Floor not found"
            )

        self.repo.soft_delete(floor)
        self.db.commit()

        return {
            "message": (
                "Floor deleted successfully"
            )
        }
