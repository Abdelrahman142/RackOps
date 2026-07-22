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


class DeviceConnector(BaseModel):
    __tablename__ = "device_connectors"

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
    connector_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    hostname: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=22,
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    encrypted_password: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
    last_connection_test: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    device = relationship("Device")
    company = relationship("Company")

    __table_args__ = (
        Index(
            "ix_device_connectors_device_id",
            "device_id",
        ),
        Index(
            "ix_device_connectors_company_id",
            "company_id",
        ),
        Index(
            "ix_device_connectors_connector_type",
            "connector_type",
        ),
    )
