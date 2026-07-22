import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PhysicalConnection(BaseModel):
    __tablename__ = "physical_connections"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    source_interface_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("network_interfaces.id"),
        nullable=False,
    )
    destination_interface_id: Mapped[uuid.UUID] = (
        mapped_column(
            UUID(as_uuid=True),
            ForeignKey("network_interfaces.id"),
            nullable=False,
        )
    )
    connection_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="COPPER",
    )
    cable_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    length_meters: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
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
    source_interface = relationship(
        "NetworkInterface",
        foreign_keys=[source_interface_id],
    )
    destination_interface = relationship(
        "NetworkInterface",
        foreign_keys=[destination_interface_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "source_interface_id",
            "destination_interface_id",
            name="uq_connection_interfaces",
        ),
        Index(
            "ix_physical_connections_company_id",
            "company_id",
        ),
        Index(
            "ix_physical_connections_source_interface_id",
            "source_interface_id",
        ),
        Index(
            "ix_physical_connections_destination_interface_id",
            "destination_interface_id",
        ),
        Index(
            "ix_physical_connections_status",
            "status",
        ),
    )
