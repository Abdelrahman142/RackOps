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


class PDU(BaseModel):
    __tablename__ = "pdus"

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
    rack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("racks.id"),
        nullable=True,
    )
    total_capacity_amp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    current_usage_amp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )
    phase_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="SINGLE",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    room = relationship(
        "Room",
        back_populates="pdus",
    )
    rack = relationship("Rack")

    __table_args__ = (
        Index(
            "ix_pdus_company_id",
            "company_id",
        ),
        Index(
            "ix_pdus_room_id",
            "room_id",
        ),
        Index(
            "ix_pdus_rack_id",
            "rack_id",
        ),
        Index(
            "ix_pdus_status",
            "status",
        ),
        Index(
            "ix_pdus_serial_number",
            "serial_number",
            unique=True,
        ),
    )
