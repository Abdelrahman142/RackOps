import math
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

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
    "country",
    "city",
    "created_at",
    "updated_at",
}


class DataCenterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DataCenterRepository(db)

    def _validate_timezone(self, timezone: str) -> None:
        try:
            ZoneInfo(timezone)
        except (KeyError, ZoneInfoNotFoundError):
            raise ValidationException(
                detail=(
                    f"Invalid timezone: '{timezone}'. "
                    "Must be a valid IANA timezone "
                    "identifier (e.g. America/New_York)"
                )
            )

    def _serialize(self, dc) -> dict:
        return {
            "id": str(dc.id),
            "company_id": str(dc.company_id),
            "name": dc.name,
            "code": dc.code,
            "country": dc.country,
            "city": dc.city,
            "address": dc.address,
            "timezone": dc.timezone,
            "status": dc.status,
            "description": dc.description,
            "latitude": dc.latitude,
            "longitude": dc.longitude,
            "created_at": dc.created_at.isoformat(),
            "updated_at": dc.updated_at.isoformat(),
        }

    def create(
        self,
        company_id: uuid.UUID,
        name: str,
        code: str,
        country: str,
        city: str,
        address: str,
        timezone: str,
        status: str = "ACTIVE",
        description: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        if status not in VALID_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    f"Must be one of: "
                    f"{', '.join(sorted(VALID_STATUSES))}"
                )
            )

        self._validate_timezone(timezone)

        if self.repo.get_by_company_and_name(
            company_id, name
        ):
            raise DuplicateException(
                detail=(
                    "A data center with this name "
                    "already exists in your company"
                )
            )

        if self.repo.get_by_company_and_code(
            company_id, code
        ):
            raise DuplicateException(
                detail=(
                    "A data center with this code "
                    "already exists in your company"
                )
            )

        dc = self.repo.create(
            company_id=company_id,
            name=name,
            code=code,
            country=country,
            city=city,
            address=address,
            timezone=timezone,
            status=status,
            description=description,
            latitude=latitude,
            longitude=longitude,
        )

        self.db.commit()
        self.db.refresh(dc)

        return self._serialize(dc)

    def get(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
    ) -> dict:
        dc = self.repo.get_active_by_company_and_id(
            company_id, datacenter_id
        )

        if not dc:
            raise NotFoundException(
                detail="Data center not found"
            )

        return self._serialize(dc)

    def list(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        country: str | None = None,
        city: str | None = None,
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
                        f"Must be one of: "
                        f"{', '.join(sorted(VALID_STATUSES))}"
                    )
                )

        if sort_by not in SORTABLE_FIELDS:
            raise ValidationException(
                detail=(
                    f"Invalid sort field: {sort_by}. "
                    f"Must be one of: "
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

        items, total = self.repo.list_by_company(
            company_id=company_id,
            status=status,
            country=country,
            city=city,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "datacenters": [
                self._serialize(dc) for dc in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
        name: str | None = None,
        code: str | None = None,
        country: str | None = None,
        city: str | None = None,
        address: str | None = None,
        timezone: str | None = None,
        status: str | None = None,
        description: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        dc = self.repo.get_active_by_company_and_id(
            company_id, datacenter_id
        )

        if not dc:
            raise NotFoundException(
                detail="Data center not found"
            )

        if status is not None:
            if status not in VALID_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        f"Must be one of: "
                        f"{', '.join(sorted(VALID_STATUSES))}"
                    )
                )

        if timezone is not None:
            self._validate_timezone(timezone)

        if name is not None and name != dc.name:
            existing = (
                self.repo.get_by_company_and_name(
                    company_id, name
                )
            )
            if existing and existing.id != dc.id:
                raise DuplicateException(
                    detail=(
                        "A data center with this name "
                        "already exists in your company"
                    )
                )

        if code is not None and code != dc.code:
            existing = (
                self.repo.get_by_company_and_code(
                    company_id, code
                )
            )
            if existing and existing.id != dc.id:
                raise DuplicateException(
                    detail=(
                        "A data center with this code "
                        "already exists in your company"
                    )
                )

        self.repo.update(
            dc,
            name=name,
            code=code,
            country=country,
            city=city,
            address=address,
            timezone=timezone,
            status=status,
            description=description,
            latitude=latitude,
            longitude=longitude,
        )

        self.db.commit()
        self.db.refresh(dc)

        return self._serialize(dc)

    def delete(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
    ) -> dict:
        dc = self.repo.get_active_by_company_and_id(
            company_id, datacenter_id
        )

        if not dc:
            raise NotFoundException(
                detail="Data center not found"
            )

        self.repo.soft_delete(dc)
        self.db.commit()

        return {
            "message": (
                "Data center deleted successfully"
            )
        }
