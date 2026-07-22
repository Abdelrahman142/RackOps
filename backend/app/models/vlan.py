import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
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


class VLAN(BaseModel):
    __tablename__ = "vlans"

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
    vlan_id: Mapped[int] = mapped_column(
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
        default="ACTIVE",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    company = relationship("Company")
    datacenter = relationship("DataCenter")
    subnets = relationship(
        "Subnet",
        back_populates="vlan",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "vlan_id",
            name="uq_vlan_company_vlan_id",
        ),
        Index(
            "ix_vlans_company_id",
            "company_id",
        ),
        Index(
            "ix_vlans_datacenter_id",
            "datacenter_id",
        ),
        Index(
            "ix_vlans_vlan_id",
            "vlan_id",
        ),
        Index(
            "ix_vlans_status",
            "status",
        ),
    )
