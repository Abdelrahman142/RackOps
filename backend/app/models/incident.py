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


class AlertIncident(BaseModel):
    __tablename__ = "incidents"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
    )
    assigned_user_id: Mapped[uuid.UUID | None] = (
        mapped_column(
            UUID(as_uuid=True),
            ForeignKey("users.id"),
            nullable=True,
        )
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    company = relationship("Company")
    alert = relationship(
        "Alert", back_populates="incident"
    )
    assigned_user = relationship("User")

    __table_args__ = (
        Index(
            "ix_incidents_company_id",
            "company_id",
        ),
        Index(
            "ix_incidents_alert_id",
            "alert_id",
        ),
        Index(
            "ix_incidents_status",
            "status",
        ),
        Index(
            "ix_incidents_priority",
            "priority",
        ),
        Index(
            "ix_incidents_assigned_user_id",
            "assigned_user_id",
        ),
        Index(
            "ix_incidents_company_status",
            "company_id",
            "status",
        ),
    )
