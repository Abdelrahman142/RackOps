import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Subnet(BaseModel):
    __tablename__ = "subnets"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    vlan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vlans.id"),
        nullable=False,
    )
    network_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
    )
    cidr: Mapped[int] = mapped_column(
        nullable=False,
    )
    gateway: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
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
    vlan = relationship(
        "VLAN",
        back_populates="subnets",
    )
    ip_addresses = relationship(
        "IPAddress",
        back_populates="subnet",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "network_address",
            "cidr",
            name="uq_subnet_company_network_cidr",
        ),
        Index(
            "ix_subnets_company_id",
            "company_id",
        ),
        Index(
            "ix_subnets_vlan_id",
            "vlan_id",
        ),
    )
