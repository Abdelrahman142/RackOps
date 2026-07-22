import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class NetworkInterface(BaseModel):
    __tablename__ = "network_interfaces"

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
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    interface_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ETHERNET",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="UP",
    )
    mac_address: Mapped[str | None] = mapped_column(
        String(17),
        nullable=True,
        unique=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    speed_mbps: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    device = relationship(
        "Device",
        back_populates="interfaces",
    )

    __table_args__ = (
        Index(
            "ix_net_interfaces_company_id",
            "company_id",
        ),
        Index(
            "ix_net_interfaces_device_id",
            "device_id",
        ),
        Index(
            "ix_net_interfaces_status",
            "status",
        ),
        Index(
            "ix_net_interfaces_interface_type",
            "interface_type",
        ),
        Index(
            "ix_net_interfaces_mac_address",
            "mac_address",
            unique=True,
        ),
    )
