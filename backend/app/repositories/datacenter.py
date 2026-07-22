import math
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.datacenter import DataCenter


class DataCenterRepository:
    def __init__(self, db: Session):
        self.db = db

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
    ) -> DataCenter:
        dc = DataCenter(
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
        self.db.add(dc)
        self.db.flush()
        return dc

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
    ) -> DataCenter | None:
        return (
            self.db.query(DataCenter)
            .filter(
                DataCenter.id == datacenter_id,
                DataCenter.company_id == company_id,
                DataCenter.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_company_and_name(
        self,
        company_id: uuid.UUID,
        name: str,
    ) -> DataCenter | None:
        return (
            self.db.query(DataCenter)
            .filter(
                DataCenter.company_id == company_id,
                DataCenter.name == name,
                DataCenter.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_company_and_code(
        self,
        company_id: uuid.UUID,
        code: str,
    ) -> DataCenter | None:
        return (
            self.db.query(DataCenter)
            .filter(
                DataCenter.company_id == company_id,
                DataCenter.code == code,
                DataCenter.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_company(
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
    ) -> tuple[list[DataCenter], int]:
        query = self.db.query(DataCenter).filter(
            DataCenter.company_id == company_id,
            DataCenter.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                DataCenter.status == status
            )

        if country is not None:
            query = query.filter(
                DataCenter.country == country
            )

        if city is not None:
            query = query.filter(
                DataCenter.city == city
            )

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                DataCenter.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            DataCenter, sort_by, DataCenter.created_at
        )
        if sort_order == "asc":
            query = query.order_by(
                sort_column.asc()
            )
        else:
            query = query.order_by(
                sort_column.desc()
            )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def update(
        self,
        datacenter: DataCenter,
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
    ) -> DataCenter:
        if name is not None:
            datacenter.name = name
        if code is not None:
            datacenter.code = code
        if country is not None:
            datacenter.country = country
        if city is not None:
            datacenter.city = city
        if address is not None:
            datacenter.address = address
        if timezone is not None:
            datacenter.timezone = timezone
        if status is not None:
            datacenter.status = status
        if description is not None:
            datacenter.description = description
        if latitude is not None:
            datacenter.latitude = latitude
        if longitude is not None:
            datacenter.longitude = longitude
        self.db.flush()
        return datacenter

    def soft_delete(
        self, datacenter: DataCenter
    ) -> DataCenter:
        datacenter.deleted_at = datetime.utcnow()
        self.db.flush()
        return datacenter
