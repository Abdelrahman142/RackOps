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


class Sensor(BaseModel):
    __tablename__ = "sensors"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environmental_zones.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    sensor_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    location_description: Mapped[str | None] = (
        mapped_column(
            String(500),
            nullable=True,
        )
    )
    last_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    last_unit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    last_reading_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime,
            nullable=True,
        )
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    zone = relationship(
        "EnvironmentalZone",
        back_populates="sensors",
    )

    __table_args__ = (
        Index(
            "ix_sensors_company_id",
            "company_id",
        ),
        Index(
            "ix_sensors_zone_id",
            "zone_id",
        ),
        Index(
            "ix_sensors_sensor_type",
            "sensor_type",
        ),
        Index(
            "ix_sensors_status",
            "status",
        ),
    )
