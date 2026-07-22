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


class Floor(BaseModel):
    __tablename__ = "floors"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id"),
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
    floor_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
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
    total_area_sqm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    building = relationship(
        "Building",
        back_populates="floors",
    )
    rooms = relationship(
        "Room",
        back_populates="floor",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "name",
            name="uq_floor_building_name",
        ),
        UniqueConstraint(
            "building_id",
            "code",
            name="uq_floor_building_code",
        ),
        UniqueConstraint(
            "building_id",
            "floor_number",
            name="uq_floor_building_floor_number",
        ),
        Index(
            "ix_floors_company_id",
            "company_id",
        ),
        Index(
            "ix_floors_building_id",
            "building_id",
        ),
        Index(
            "ix_floors_status",
            "status",
        ),
    )
