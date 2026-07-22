import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.metric_data import MetricData


class MetricDataRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        target_id: uuid.UUID,
        metric_definition_id: uuid.UUID,
        value: float,
        timestamp: datetime,
    ) -> MetricData:
        metric = MetricData(
            company_id=company_id,
            device_id=device_id,
            target_id=target_id,
            metric_definition_id=metric_definition_id,
            value=value,
            timestamp=timestamp,
        )
        self.db.add(metric)
        self.db.flush()
        return metric

    def get_by_id(
        self,
        metric_id: uuid.UUID,
    ) -> MetricData | None:
        return (
            self.db.query(MetricData)
            .filter(MetricData.id == metric_id)
            .first()
        )

    def list_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        metric_definition_id: uuid.UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        size: int = 100,
    ) -> tuple[list[MetricData], int]:
        query = self.db.query(MetricData).filter(
            MetricData.company_id == company_id,
            MetricData.device_id == device_id,
        )

        if metric_definition_id is not None:
            query = query.filter(
                MetricData.metric_definition_id
                == metric_definition_id
            )

        if start_time is not None:
            query = query.filter(
                MetricData.timestamp >= start_time
            )

        if end_time is not None:
            query = query.filter(
                MetricData.timestamp <= end_time
            )

        total = query.count()
        query = query.order_by(
            MetricData.timestamp.desc()
        )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def get_latest_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> list[MetricData]:
        subq = (
            self.db.query(
                MetricData.metric_definition_id,
                func.max(MetricData.timestamp).label(
                    "max_ts"
                ),
            )
            .filter(
                MetricData.company_id == company_id,
                MetricData.device_id == device_id,
            )
            .group_by(
                MetricData.metric_definition_id
            )
            .subquery()
        )

        return (
            self.db.query(MetricData)
            .join(
                subq,
                (MetricData.metric_definition_id == subq.c.metric_definition_id)  # noqa: E501
                & (MetricData.timestamp == subq.c.max_ts),
            )
            .filter(
                MetricData.company_id == company_id,
                MetricData.device_id == device_id,
            )
            .all()
        )

    def get_average_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        metric_definition_id: uuid.UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> float | None:
        query = self.db.query(
            func.avg(MetricData.value)
        ).filter(
            MetricData.company_id == company_id,
            MetricData.device_id == device_id,
            MetricData.metric_definition_id
            == metric_definition_id,
        )

        if start_time is not None:
            query = query.filter(
                MetricData.timestamp >= start_time
            )

        if end_time is not None:
            query = query.filter(
                MetricData.timestamp <= end_time
            )

        result = query.scalar()

        if result is None:
            return None

        return round(float(result), 2)

    def get_average_by_device_metric_key(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        metric_key: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> float | None:
        from app.models.metric_definition import (
            MetricDefinition,
        )

        metric_def = (
            self.db.query(MetricDefinition)
            .filter(
                MetricDefinition.metric_key == metric_key
            )
            .first()
        )

        if not metric_def:
            return None

        return self.get_average_by_device(
            company_id=company_id,
            device_id=device_id,
            metric_definition_id=metric_def.id,
            start_time=start_time,
            end_time=end_time,
        )

    def get_average_for_devices(
        self,
        company_id: uuid.UUID,
        device_ids: list[uuid.UUID],
        metric_key: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> float | None:
        if not device_ids:
            return None

        from app.models.metric_definition import (
            MetricDefinition,
        )

        metric_def = (
            self.db.query(MetricDefinition)
            .filter(
                MetricDefinition.metric_key == metric_key
            )
            .first()
        )

        if not metric_def:
            return None

        query = self.db.query(
            func.avg(MetricData.value)
        ).filter(
            MetricData.company_id == company_id,
            MetricData.device_id.in_(device_ids),
            MetricData.metric_definition_id
            == metric_def.id,
        )

        if start_time is not None:
            query = query.filter(
                MetricData.timestamp >= start_time
            )

        if end_time is not None:
            query = query.filter(
                MetricData.timestamp <= end_time
            )

        result = query.scalar()

        if result is None:
            return None

        return round(float(result), 2)

    def count_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> int:
        return (
            self.db.query(MetricData)
            .filter(
                MetricData.company_id == company_id,
                MetricData.device_id == device_id,
            )
            .count()
        )

    def delete_old_data(
        self,
        company_id: uuid.UUID,
        older_than: datetime,
    ) -> int:
        count = (
            self.db.query(MetricData)
            .filter(
                MetricData.company_id == company_id,
                MetricData.timestamp < older_than,
            )
            .delete()
        )
        self.db.flush()
        return count
