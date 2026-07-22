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


class AutomationJob(BaseModel):
    __tablename__ = "automation_jobs"

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
    job_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    company = relationship("Company")
    creator = relationship("User")
    tasks = relationship(
        "AutomationTask",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_automation_jobs_company_id",
            "company_id",
        ),
        Index(
            "ix_automation_jobs_status",
            "status",
        ),
        Index(
            "ix_automation_jobs_job_type",
            "job_type",
        ),
        Index(
            "ix_automation_jobs_created_by",
            "created_by",
        ),
    )
