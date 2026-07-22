import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.power_feed import PowerFeed


class PowerFeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
        destination_type: str,
        destination_id: uuid.UUID,
        voltage: float,
        amp_rating: float,
        status: str = "ACTIVE",
    ) -> PowerFeed:
        feed = PowerFeed(
            company_id=company_id,
            source_type=source_type,
            source_id=source_id,
            destination_type=destination_type,
            destination_id=destination_id,
            voltage=voltage,
            amp_rating=amp_rating,
            status=status,
        )
        self.db.add(feed)
        self.db.flush()
        return feed

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        feed_id: uuid.UUID,
    ) -> PowerFeed | None:
        return (
            self.db.query(PowerFeed)
            .filter(
                PowerFeed.id == feed_id,
                PowerFeed.company_id == company_id,
                PowerFeed.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_connection(
        self,
        source_type: str,
        source_id: uuid.UUID,
        destination_type: str,
        destination_id: uuid.UUID,
    ) -> PowerFeed | None:
        return (
            self.db.query(PowerFeed)
            .filter(
                PowerFeed.source_type == source_type,
                PowerFeed.source_id == source_id,
                PowerFeed.destination_type == destination_type,
                PowerFeed.destination_id == destination_id,
                PowerFeed.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        source_type: str | None = None,
        destination_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[PowerFeed], int]:
        query = self.db.query(PowerFeed).filter(
            PowerFeed.company_id == company_id,
            PowerFeed.deleted_at.is_(None),
        )

        if source_type is not None:
            query = query.filter(
                PowerFeed.source_type == source_type
            )

        if destination_type is not None:
            query = query.filter(
                PowerFeed.destination_type == destination_type
            )

        if status is not None:
            query = query.filter(
                PowerFeed.status == status
            )

        total = query.count()
        query = query.order_by(PowerFeed.created_at.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_by_source(
        self,
        source_type: str,
        source_id: uuid.UUID,
    ) -> list[PowerFeed]:
        return (
            self.db.query(PowerFeed)
            .filter(
                PowerFeed.source_type == source_type,
                PowerFeed.source_id == source_id,
                PowerFeed.deleted_at.is_(None),
            )
            .all()
        )

    def list_by_destination(
        self,
        destination_type: str,
        destination_id: uuid.UUID,
    ) -> list[PowerFeed]:
        return (
            self.db.query(PowerFeed)
            .filter(
                PowerFeed.destination_type == destination_type,
                PowerFeed.destination_id == destination_id,
                PowerFeed.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        feed: PowerFeed,
        voltage: float | None = None,
        amp_rating: float | None = None,
        status: str | None = None,
    ) -> PowerFeed:
        if voltage is not None:
            feed.voltage = voltage
        if amp_rating is not None:
            feed.amp_rating = amp_rating
        if status is not None:
            feed.status = status
        self.db.flush()
        return feed

    def soft_delete(self, feed: PowerFeed) -> PowerFeed:
        feed.deleted_at = datetime.utcnow()
        self.db.flush()
        return feed
