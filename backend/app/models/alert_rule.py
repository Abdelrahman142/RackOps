import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AlertRule(BaseModel):
    __tablename__ = "alert_rules"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    metric_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    condition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    threshold_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="WARNING",
    )
    enabled: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    evaluation_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    company = relationship("Company")
    alerts = relationship(
        "Alert", back_populates="rule", lazy="select"
    )

    __table_args__ = (
        Index(
            "ix_alert_rules_company_id",
            "company_id",
        ),
        Index(
            "ix_alert_rules_metric_key",
            "metric_key",
        ),
        Index(
            "ix_alert_rules_enabled",
            "enabled",
        ),
        Index(
            "ix_alert_rules_severity",
            "severity",
        ),
        Index(
            "ix_alert_rules_deleted_at",
            "deleted_at",
        ),
        Index(
            "ix_alert_rules_company_metric",
            "company_id",
            "metric_key",
        ),
    )
