import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Alert(BaseModel):
    __tablename__ = "alerts"

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
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alert_rules.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    company = relationship("Company")
    device = relationship("Device")
    rule = relationship(
        "AlertRule", back_populates="alerts"
    )
    incident = relationship(
        "AlertIncident",
        back_populates="alert",
        uselist=False,
        lazy="select",
    )

    __table_args__ = (
        Index(
            "ix_alerts_company_id",
            "company_id",
        ),
        Index(
            "ix_alerts_device_id",
            "device_id",
        ),
        Index(
            "ix_alerts_rule_id",
            "rule_id",
        ),
        Index(
            "ix_alerts_status",
            "status",
        ),
        Index(
            "ix_alerts_severity",
            "severity",
        ),
        Index(
            "ix_alerts_triggered_at",
            "triggered_at",
        ),
        Index(
            "ix_alerts_company_status",
            "company_id",
            "status",
        ),
        Index(
            "ix_alerts_company_device",
            "company_id",
            "device_id",
        ),
        Index(
            "ix_alerts_open_by_rule",
            "rule_id",
            "device_id",
            "status",
        ),
    )
