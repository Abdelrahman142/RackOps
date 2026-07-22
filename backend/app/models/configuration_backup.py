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


class ConfigurationBackup(BaseModel):
    __tablename__ = "configuration_backups"

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
    backup_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    location: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    size: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    checksum: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
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

    device = relationship("Device")
    company = relationship("Company")
    creator = relationship("User")

    __table_args__ = (
        Index(
            "ix_config_backups_device_id",
            "device_id",
        ),
        Index(
            "ix_config_backups_company_id",
            "company_id",
        ),
        Index(
            "ix_config_backups_status",
            "status",
        ),
        Index(
            "ix_config_backups_backup_type",
            "backup_type",
        ),
    )
