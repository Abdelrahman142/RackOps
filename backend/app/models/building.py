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


class Building(BaseModel):
    __tablename__ = "buildings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    datacenter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datacenters.id"),
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
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    number_of_floors: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    total_area: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    power_capacity_kw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    cooling_capacity_kw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    datacenter = relationship(
        "DataCenter",
        back_populates="buildings",
    )
    floors = relationship(
        "Floor",
        back_populates="building",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "datacenter_id",
            "name",
            name="uq_building_datacenter_name",
        ),
        UniqueConstraint(
            "datacenter_id",
            "code",
            name="uq_building_datacenter_code",
        ),
        Index(
            "ix_buildings_company_id",
            "company_id",
        ),
        Index(
            "ix_buildings_datacenter_id",
            "datacenter_id",
        ),
        Index(
            "ix_buildings_status",
            "status",
        ),
    )
