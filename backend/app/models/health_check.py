import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class HealthCheck(BaseModel):
    __tablename__ = "health_checks"

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
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="UNKNOWN",
    )
    response_time_ms: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    company = relationship("Company")
    device = relationship("Device")

    __table_args__ = (
        Index(
            "ix_health_checks_company_id",
            "company_id",
        ),
        Index(
            "ix_health_checks_device_id",
            "device_id",
        ),
        Index(
            "ix_health_checks_status",
            "status",
        ),
        Index(
            "ix_health_checks_checked_at",
            "checked_at",
        ),
        Index(
            "ix_health_checks_device_checked",
            "device_id",
            "checked_at",
        ),
    )
