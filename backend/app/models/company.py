from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Company(BaseModel):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    users = relationship(
        "User",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    datacenters = relationship(
        "DataCenter",
        back_populates="company",
        cascade="all, delete-orphan",
    )
