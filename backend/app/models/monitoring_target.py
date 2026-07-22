import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MonitoringTarget(BaseModel):
    __tablename__ = "monitoring_targets"

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
    enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
    collector_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="AGENT",
    )
    endpoint: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    interval_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )
    last_check_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    device = relationship("Device")
    metric_data = relationship(
        "MetricData",
        back_populates="target",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_monitoring_targets_company_id",
            "company_id",
        ),
        Index(
            "ix_monitoring_targets_device_id",
            "device_id",
        ),
        Index(
            "ix_monitoring_targets_status",
            "status",
        ),
        Index(
            "ix_monitoring_targets_collector_type",
            "collector_type",
        ),
        Index(
            "ix_monitoring_targets_enabled",
            "enabled",
        ),
    )
