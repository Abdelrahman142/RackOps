import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PowerFeed(BaseModel):
    __tablename__ = "power_feeds"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    destination_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    destination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    voltage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    amp_rating: Mapped[float] = mapped_column(
        Float,
        nullable=False,
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

    __table_args__ = (
        Index(
            "ix_power_feeds_company_id",
            "company_id",
        ),
        Index(
            "ix_power_feeds_source",
            "source_type",
            "source_id",
        ),
        Index(
            "ix_power_feeds_destination",
            "destination_type",
            "destination_id",
        ),
        Index(
            "ix_power_feeds_status",
            "status",
        ),
        UniqueConstraint(
            "source_type",
            "source_id",
            "destination_type",
            "destination_id",
            name="uq_power_feed_connection",
        ),
    )
