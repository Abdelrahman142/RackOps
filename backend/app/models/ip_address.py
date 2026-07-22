import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class IPAddress(BaseModel):
    __tablename__ = "ip_addresses"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    subnet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subnets.id"),
        nullable=False,
    )
    device_interface_id: Mapped[uuid.UUID | None] = (
        mapped_column(
            UUID(as_uuid=True),
            ForeignKey("network_interfaces.id"),
            nullable=True,
        )
    )
    address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="AVAILABLE",
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
    subnet = relationship(
        "Subnet",
        back_populates="ip_addresses",
    )
    device_interface = relationship(
        "NetworkInterface",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "address",
            name="uq_ip_address_company_address",
        ),
        Index(
            "ix_ip_addresses_company_id",
            "company_id",
        ),
        Index(
            "ix_ip_addresses_subnet_id",
            "subnet_id",
        ),
        Index(
            "ix_ip_addresses_device_interface_id",
            "device_interface_id",
        ),
        Index(
            "ix_ip_addresses_status",
            "status",
        ),
        Index(
            "ix_ip_addresses_address",
            "address",
        ),
    )
