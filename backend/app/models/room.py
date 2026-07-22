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


class Room(BaseModel):
    __tablename__ = "rooms"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    floor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("floors.id"),
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
    room_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="SERVER_ROOM",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PLANNED",
    )
    area_sqm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    height_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    max_rack_capacity: Mapped[int | None] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )
    max_power_capacity_kw: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    max_cooling_capacity_kw: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    temperature_min: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    temperature_max: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    humidity_min: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    humidity_max: Mapped[float | None] = (
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
    floor = relationship(
        "Floor",
        back_populates="rooms",
    )
    racks = relationship(
        "Rack",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    ups_systems = relationship(
        "UPS",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    pdus = relationship(
        "PDU",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    cooling_units = relationship(
        "CoolingUnit",
        back_populates="room",
        cascade="all, delete-orphan",
    )
    zones = relationship(
        "EnvironmentalZone",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "floor_id",
            "name",
            name="uq_room_floor_name",
        ),
        UniqueConstraint(
            "floor_id",
            "code",
            name="uq_room_floor_code",
        ),
        Index(
            "ix_rooms_company_id",
            "company_id",
        ),
        Index(
            "ix_rooms_floor_id",
            "floor_id",
        ),
        Index(
            "ix_rooms_status",
            "status",
        ),
        Index(
            "ix_rooms_room_type",
            "room_type",
        ),
    )
