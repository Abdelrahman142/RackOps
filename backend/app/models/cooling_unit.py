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


class CoolingUnit(BaseModel):
    __tablename__ = "cooling_units"

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
    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CRAC",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    cooling_capacity_kw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    airflow_cfm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    power_consumption_kw: Mapped[float | None] = (
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
        back_populates="cooling_units",
    )

    __table_args__ = (
        Index(
            "ix_cooling_units_company_id",
            "company_id",
        ),
        Index(
            "ix_cooling_units_room_id",
            "room_id",
        ),
        Index(
            "ix_cooling_units_status",
            "status",
        ),
        Index(
            "ix_cooling_units_type",
            "type",
        ),
        Index(
            "ix_cooling_units_serial_number",
            "serial_number",
            unique=True,
        ),
    )
