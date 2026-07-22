import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.metric_definition import (
    MetricDefinition,
)


class MetricDefinitionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        metric_key: str,
        unit: str | None = None,
        description: str | None = None,
        category: str = "OTHER",
    ) -> MetricDefinition:
        definition = MetricDefinition(
            name=name,
            metric_key=metric_key,
            unit=unit,
            description=description,
            category=category,
        )
        self.db.add(definition)
        self.db.flush()
        return definition

    def get_by_id(
        self,
        definition_id: uuid.UUID,
    ) -> MetricDefinition | None:
        return (
            self.db.query(MetricDefinition)
            .filter(
                MetricDefinition.id == definition_id
            )
            .first()
        )

    def get_by_metric_key(
        self,
        metric_key: str,
    ) -> MetricDefinition | None:
        return (
            self.db.query(MetricDefinition)
            .filter(
                MetricDefinition.metric_key == metric_key
            )
            .first()
        )

    def list_by_category(
        self,
        category: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[MetricDefinition], int]:
        query = self.db.query(MetricDefinition)

        if category is not None:
            query = query.filter(
                MetricDefinition.category == category
            )

        total = query.count()
        query = query.order_by(
            MetricDefinition.name.asc()
        )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_all(
        self,
    ) -> list[MetricDefinition]:
        return (
            self.db.query(MetricDefinition)
            .order_by(MetricDefinition.name.asc())
            .all()
        )
