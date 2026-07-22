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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UPS(BaseModel):
    __tablename__ = "ups_systems"

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
    model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    manufacturer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    capacity_kva: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    battery_capacity_minutes: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )
    input_voltage: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    output_voltage: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    efficiency_percent: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    room = relationship(
        "Room",
        back_populates="ups_systems",
    )
    power_feeds = relationship(
        "PowerFeed",
        primaryjoin=(
            "(UPS.id == PowerFeed.source_id) & "
            "(PowerFeed.source_type == 'UPS')"
        ),
        foreign_keys="PowerFeed.source_id",
        viewonly=True,
    )

    __table_args__ = (
        Index(
            "ix_ups_company_id",
            "company_id",
        ),
        Index(
            "ix_ups_room_id",
            "room_id",
        ),
        Index(
            "ix_ups_status",
            "status",
        ),
        Index(
            "ix_ups_serial_number",
            "serial_number",
            unique=True,
        ),
    )
