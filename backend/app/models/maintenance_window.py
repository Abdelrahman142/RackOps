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


class MaintenanceWindow(BaseModel):
    __tablename__ = "maintenance_windows"

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
    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SCHEDULED",
    )

    company = relationship("Company")
    creator = relationship("User")

    __table_args__ = (
        Index(
            "ix_maintenance_windows_company_id",
            "company_id",
        ),
        Index(
            "ix_maintenance_windows_status",
            "status",
        ),
        Index(
            "ix_maintenance_windows_start_time",
            "start_time",
        ),
        Index(
            "ix_maintenance_windows_end_time",
            "end_time",
        ),
        Index(
            "ix_maintenance_windows_company_status",
            "company_id",
            "status",
        ),
    )
