import uuid
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.maintenance_window import (
    MaintenanceWindow,
)


class MaintenanceWindowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        name: str,
        start_time: datetime,
        end_time: datetime,
        created_by: uuid.UUID,
        description: str | None = None,
    ) -> MaintenanceWindow:
        window = MaintenanceWindow(
            company_id=company_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            created_by=created_by,
            description=description,
        )
        self.db.add(window)
        self.db.flush()
        return window

    def get_by_id(
        self,
        company_id: uuid.UUID,
        window_id: uuid.UUID,
    ) -> MaintenanceWindow | None:
        return (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.id == window_id,
                MaintenanceWindow.company_id
                == company_id,
            )
            .first()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[MaintenanceWindow], int]:
        query = self.db.query(
            MaintenanceWindow
        ).filter(
            MaintenanceWindow.company_id == company_id,
        )

        if status is not None:
            query = query.filter(
                MaintenanceWindow.status == status
            )

        total = query.count()
        query = query.order_by(
            MaintenanceWindow.start_time.desc()
        )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def get_active_window(
        self,
        company_id: uuid.UUID,
        at_time: datetime | None = None,
    ) -> MaintenanceWindow | None:
        if at_time is None:
            at_time = datetime.utcnow()

        return (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.company_id
                == company_id,
                MaintenanceWindow.status.in_(
                    ["SCHEDULED", "ACTIVE"]
                ),
                MaintenanceWindow.start_time <= at_time,
                MaintenanceWindow.end_time >= at_time,
            )
            .first()
        )

    def update(
        self,
        window: MaintenanceWindow,
        **kwargs,
    ) -> MaintenanceWindow:
        for key, value in kwargs.items():
            if value is not None:
                setattr(window, key, value)
        self.db.flush()
        return window

    def delete(
        self,
        company_id: uuid.UUID,
        window_id: uuid.UUID,
    ) -> bool:
        window = self.get_by_id(company_id, window_id)
        if not window:
            return False
        self.db.delete(window)
        self.db.flush()
        return True

    def has_active_window(
        self,
        company_id: uuid.UUID,
    ) -> bool:
        now = datetime.utcnow()
        return (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.company_id
                == company_id,
                MaintenanceWindow.status.in_(
                    ["SCHEDULED", "ACTIVE"]
                ),
                MaintenanceWindow.start_time <= now,
                MaintenanceWindow.end_time >= now,
            )
            .first()
            is not None
        )
