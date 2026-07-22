import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.monitoring_target import (
    MonitoringTarget,
)


class MonitoringTargetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        enabled: bool = True,
        collector_type: str = "AGENT",
        endpoint: str | None = None,
        port: int | None = None,
        interval_seconds: int = 60,
        status: str = "PENDING",
    ) -> MonitoringTarget:
        target = MonitoringTarget(
            company_id=company_id,
            device_id=device_id,
            enabled=enabled,
            collector_type=collector_type,
            endpoint=endpoint,
            port=port,
            interval_seconds=interval_seconds,
            status=status,
        )
        self.db.add(target)
        self.db.flush()
        return target

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> MonitoringTarget | None:
        return (
            self.db.query(MonitoringTarget)
            .filter(
                MonitoringTarget.id == target_id,
                MonitoringTarget.company_id == company_id,
                MonitoringTarget.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> MonitoringTarget | None:
        return (
            self.db.query(MonitoringTarget)
            .filter(
                MonitoringTarget.company_id == company_id,
                MonitoringTarget.device_id == device_id,
                MonitoringTarget.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        enabled: bool | None = None,
        collector_type: str | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[MonitoringTarget], int]:
        query = self.db.query(
            MonitoringTarget
        ).filter(
            MonitoringTarget.company_id == company_id,
            MonitoringTarget.deleted_at.is_(None),
        )

        if enabled is not None:
            query = query.filter(
                MonitoringTarget.enabled == enabled
            )

        if collector_type is not None:
            query = query.filter(
                MonitoringTarget.collector_type
                == collector_type
            )

        if status is not None:
            query = query.filter(
                MonitoringTarget.status == status
            )

        total = query.count()

        sort_column = getattr(
            MonitoringTarget,
            sort_by,
            MonitoringTarget.created_at,
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_enabled_by_company(
        self,
        company_id: uuid.UUID,
    ) -> list[MonitoringTarget]:
        return (
            self.db.query(MonitoringTarget)
            .filter(
                MonitoringTarget.company_id == company_id,
                MonitoringTarget.enabled.is_(True),
                MonitoringTarget.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        target: MonitoringTarget,
        enabled: bool | None = None,
        collector_type: str | None = None,
        endpoint: str | None = None,
        port: int | None = None,
        interval_seconds: int | None = None,
        status: str | None = None,
        last_check_at: datetime | None = None,
    ) -> MonitoringTarget:
        if enabled is not None:
            target.enabled = enabled
        if collector_type is not None:
            target.collector_type = collector_type
        if endpoint is not None:
            target.endpoint = endpoint
        if port is not None:
            target.port = port
        if interval_seconds is not None:
            target.interval_seconds = interval_seconds
        if status is not None:
            target.status = status
        if last_check_at is not None:
            target.last_check_at = last_check_at
        self.db.flush()
        return target

    def soft_delete(
        self,
        target: MonitoringTarget,
    ) -> MonitoringTarget:
        target.deleted_at = datetime.utcnow()
        self.db.flush()
        return target
