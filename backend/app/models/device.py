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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Device(BaseModel):
    __tablename__ = "devices"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    rack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("racks.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    hostname: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    device_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="SERVER",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    vendor: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    asset_tag: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    rack_unit_start: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )
    rack_unit_height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    front_or_rear: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    mac_address: Mapped[str | None] = mapped_column(
        String(17),
        nullable=True,
    )
    management_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    operating_system: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    cpu: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    memory_gb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    storage_gb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    power_consumption_watt: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )
    purchase_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    warranty_end_date: Mapped[str | None] = (
        mapped_column(
            String(10),
            nullable=True,
        )
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    rack = relationship(
        "Rack",
        back_populates="devices",
    )
    interfaces = relationship(
        "NetworkInterface",
        back_populates="device",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "name",
            name="uq_device_company_name",
        ),
        Index(
            "ix_devices_company_id",
            "company_id",
        ),
        Index(
            "ix_devices_rack_id",
            "rack_id",
        ),
        Index(
            "ix_devices_status",
            "status",
        ),
        Index(
            "ix_devices_device_type",
            "device_type",
        ),
        Index(
            "ix_devices_serial_number",
            "serial_number",
            unique=True,
        ),
        Index(
            "ix_devices_asset_tag",
            "asset_tag",
            unique=True,
        ),
    )
