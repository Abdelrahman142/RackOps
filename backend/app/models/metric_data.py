import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MetricData(BaseModel):
    __tablename__ = "metric_data"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id"),
        nullable=False,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitoring_targets.id"),
        nullable=False,
    )
    metric_definition_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            ForeignKey("metric_definitions.id"),
            nullable=False,
        )
    )
    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    company = relationship("Company")
    device = relationship("Device")
    target = relationship(
        "MonitoringTarget",
        back_populates="metric_data",
    )
    metric_definition = relationship(
        "MetricDefinition",
    )

    __table_args__ = (
        Index(
            "ix_metric_data_company_id",
            "company_id",
        ),
        Index(
            "ix_metric_data_device_id",
            "device_id",
        ),
        Index(
            "ix_metric_data_target_id",
            "target_id",
        ),
        Index(
            "ix_metric_data_metric_definition_id",
            "metric_definition_id",
        ),
        Index(
            "ix_metric_data_timestamp",
            "timestamp",
        ),
        Index(
            "ix_metric_data_device_timestamp",
            "device_id",
            "timestamp",
        ),
        Index(
            "ix_metric_data_company_device_def",
            "company_id",
            "device_id",
            "metric_definition_id",
        ),
    )
