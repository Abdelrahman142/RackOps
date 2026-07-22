import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.health_check import HealthCheck


class HealthCheckRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        status: str,
        response_time_ms: float | None = None,
        checked_at: datetime | None = None,
    ) -> HealthCheck:
        if checked_at is None:
            checked_at = datetime.utcnow()

        check = HealthCheck(
            company_id=company_id,
            device_id=device_id,
            status=status,
            response_time_ms=response_time_ms,
            checked_at=checked_at,
        )
        self.db.add(check)
        self.db.flush()
        return check

    def get_latest_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> HealthCheck | None:
        return (
            self.db.query(HealthCheck)
            .filter(
                HealthCheck.company_id == company_id,
                HealthCheck.device_id == device_id,
            )
            .order_by(
                HealthCheck.checked_at.desc()
            )
            .first()
        )

    def list_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        size: int = 100,
    ) -> tuple[list[HealthCheck], int]:
        query = self.db.query(HealthCheck).filter(
            HealthCheck.company_id == company_id,
            HealthCheck.device_id == device_id,
        )

        if status is not None:
            query = query.filter(
                HealthCheck.status == status
            )

        if start_time is not None:
            query = query.filter(
                HealthCheck.checked_at >= start_time
            )

        if end_time is not None:
            query = query.filter(
                HealthCheck.checked_at <= end_time
            )

        total = query.count()
        query = query.order_by(
            HealthCheck.checked_at.desc()
        )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def get_health_summary_by_company(
        self,
        company_id: uuid.UUID,
    ) -> dict:
        subq = (
            self.db.query(
                HealthCheck.device_id,
                func.max(HealthCheck.checked_at).label(
                    "max_checked"
                ),
            )
            .filter(
                HealthCheck.company_id == company_id
            )
            .group_by(HealthCheck.device_id)
            .subquery()
        )

        latest = (
            self.db.query(HealthCheck)
            .join(
                subq,
                (HealthCheck.device_id == subq.c.device_id)  # noqa: E501
                & (
                    HealthCheck.checked_at
                    == subq.c.max_checked
                ),
            )
            .all()
        )

        status_counts = {}
        for check in latest:
            s = check.status
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "total": len(latest),
            "statuses": status_counts,
            "online": status_counts.get("UP", 0),
            "offline": status_counts.get("DOWN", 0),
            "warning": status_counts.get("WARNING", 0),
            "unknown": status_counts.get("UNKNOWN", 0),
        }
