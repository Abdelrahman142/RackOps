import math
import uuid

from sqlalchemy.orm import Session

from app.repositories.building import BuildingRepository
from app.repositories.datacenter import DataCenterRepository
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
    "status",
    "created_at",
    "updated_at",
}


class BuildingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BuildingRepository(db)
        self.dc_repo = DataCenterRepository(db)

    def _serialize(self, building) -> dict:
        return {
            "id": str(building.id),
            "company_id": str(building.company_id),
            "datacenter_id": str(building.datacenter_id),
            "name": building.name,
            "code": building.code,
            "description": building.description,
            "status": building.status,
            "address": building.address,
            "number_of_floors": building.number_of_floors,
            "total_area": building.total_area,
            "power_capacity_kw": building.power_capacity_kw,
            "cooling_capacity_kw": (
                building.cooling_capacity_kw
            ),
            "created_at": building.created_at.isoformat(),
            "updated_at": building.updated_at.isoformat(),
        }

    def create(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        name: str,
        code: str,
        address: str,
        status: str = "PLANNED",
        description: str | None = None,
        number_of_floors: int = 1,
        total_area: float | None = None,
        power_capacity_kw: float | None = None,
        cooling_capacity_kw: float | None = None,
    ) -> dict:
        if status not in VALID_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_STATUSES))}"
                )
            )

        if not self.dc_repo.get_active_by_company_and_id(
            company_id, datacenter_id
        ):
            raise NotFoundException(
                detail="Data center not found"
            )

        if self.repo.get_by_datacenter_and_name(
            datacenter_id, name
        ):
            raise DuplicateException(
                detail=(
                    "A building with this name "
                    "already exists in this data center"
                )
            )

        if self.repo.get_by_datacenter_and_code(
            datacenter_id, code
        ):
            raise DuplicateException(
                detail=(
                    "A building with this code "
                    "already exists in this data center"
                )
            )

        building = self.repo.create(
            company_id=company_id,
            datacenter_id=datacenter_id,
            name=name,
            code=code,
            address=address,
            status=status,
            description=description,
            number_of_floors=number_of_floors,
            total_area=total_area,
            power_capacity_kw=power_capacity_kw,
            cooling_capacity_kw=cooling_capacity_kw,
        )

        self.db.commit()
        self.db.refresh(building)

        return self._serialize(building)

    def get(
        self,
        company_id: uuid.UUID,
        building_id: uuid.UUID,
    ) -> dict:
        building = self.repo.get_active_by_company_and_id(
            company_id, building_id
        )

        if not building:
            raise NotFoundException(
                detail="Building not found"
            )

        return self._serialize(building)

    def list_by_datacenter(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        status: str | None = None,
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

        items, total = self.repo.list_by_datacenter(
            company_id=company_id,
            datacenter_id=datacenter_id,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "buildings": [
                self._serialize(b) for b in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update(
        self,
        company_id: uuid.UUID,
        building_id: uuid.UUID,
        name: str | None = None,
        code: str | None = None,
        address: str | None = None,
        status: str | None = None,
        description: str | None = None,
        number_of_floors: int | None = None,
        total_area: float | None = None,
        power_capacity_kw: float | None = None,
        cooling_capacity_kw: float | None = None,
    ) -> dict:
        building = self.repo.get_active_by_company_and_id(
            company_id, building_id
        )

        if not building:
            raise NotFoundException(
                detail="Building not found"
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

        if name is not None and name != building.name:
            existing = (
                self.repo.get_by_datacenter_and_name(
                    building.datacenter_id, name
                )
            )
            if existing and existing.id != building.id:
                raise DuplicateException(
                    detail=(
                        "A building with this name "
                        "already exists in this data center"
                    )
                )

        if code is not None and code != building.code:
            existing = (
                self.repo.get_by_datacenter_and_code(
                    building.datacenter_id, code
                )
            )
            if existing and existing.id != building.id:
                raise DuplicateException(
                    detail=(
                        "A building with this code "
                        "already exists in this data center"
                    )
                )

        self.repo.update(
            building,
            name=name,
            code=code,
            address=address,
            status=status,
            description=description,
            number_of_floors=number_of_floors,
            total_area=total_area,
            power_capacity_kw=power_capacity_kw,
            cooling_capacity_kw=cooling_capacity_kw,
        )

        self.db.commit()
        self.db.refresh(building)

        return self._serialize(building)

    def delete(
        self,
        company_id: uuid.UUID,
        building_id: uuid.UUID,
    ) -> dict:
        building = self.repo.get_active_by_company_and_id(
            company_id, building_id
        )

        if not building:
            raise NotFoundException(
                detail="Building not found"
            )

        self.repo.soft_delete(building)
        self.db.commit()

        return {
            "message": (
                "Building deleted successfully"
            )
        }
