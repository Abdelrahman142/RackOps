import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class MetricDefinition(BaseModel):
    __tablename__ = "metric_definitions"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    metric_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OTHER",
    )

    __table_args__ = (
        Index(
            "ix_metric_definitions_metric_key",
            "metric_key",
            unique=True,
        ),
        Index(
            "ix_metric_definitions_category",
            "category",
        ),
        Index(
            "ix_metric_definitions_name",
            "name",
        ),
    )
