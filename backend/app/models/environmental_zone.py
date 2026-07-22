import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class EnvironmentalZone(BaseModel):
    __tablename__ = "environmental_zones"

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
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    target_temperature_min: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    target_temperature_max: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    target_humidity_min: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    target_humidity_max: Mapped[float | None] = (
        mapped_column(
            Float,
            nullable=True,
        )
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    room = relationship(
        "Room",
        back_populates="zones",
    )
    sensors = relationship(
        "Sensor",
        back_populates="zone",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_env_zones_company_id",
            "company_id",
        ),
        Index(
            "ix_env_zones_room_id",
            "room_id",
        ),
        Index(
            "ix_env_zones_status",
            "status",
        ),
    )
