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


class Rack(BaseModel):
    __tablename__ = "racks"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rack_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="SERVER_RACK",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    height_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=42,
    )
    width_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    depth_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    max_weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    current_weight_kg: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
            default=0,
        )
    )
    power_capacity_kw: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    current_power_usage_kw: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
            default=0,
        )
    )
    cooling_capacity_kw: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    manufacturer: Mapped[str | None] = mapped_column(
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
    position_in_room: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
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
    room = relationship(
        "Room",
        back_populates="racks",
    )
    devices = relationship(
        "Device",
        back_populates="rack",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "name",
            name="uq_rack_room_name",
        ),
        UniqueConstraint(
            "room_id",
            "code",
            name="uq_rack_room_code",
        ),
        Index(
            "ix_racks_company_id",
            "company_id",
        ),
        Index(
            "ix_racks_room_id",
            "room_id",
        ),
        Index(
            "ix_racks_status",
            "status",
        ),
        Index(
            "ix_racks_rack_type",
            "rack_type",
        ),
        Index(
            "ix_racks_serial_number",
            "serial_number",
            unique=True,
        ),
    )
