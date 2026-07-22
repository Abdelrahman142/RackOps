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


class AutomationTask(BaseModel):
    __tablename__ = "automation_tasks"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automation_jobs.id"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    command: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    parameters: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )
    output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    job = relationship(
        "AutomationJob",
        back_populates="tasks",
    )
    device = relationship("Device")
    company = relationship("Company")

    __table_args__ = (
        Index(
            "ix_automation_tasks_job_id",
            "job_id",
        ),
        Index(
            "ix_automation_tasks_device_id",
            "device_id",
        ),
        Index(
            "ix_automation_tasks_company_id",
            "company_id",
        ),
        Index(
            "ix_automation_tasks_status",
            "status",
        ),
    )
