import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.incident import AlertIncident


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
        title: str,
        description: str | None = None,
        priority: str = "MEDIUM",
        assigned_user_id: uuid.UUID | None = None,
    ) -> AlertIncident:
        incident = AlertIncident(
            company_id=company_id,
            alert_id=alert_id,
            title=title,
            description=description,
            priority=priority,
            assigned_user_id=assigned_user_id,
        )
        self.db.add(incident)
        self.db.flush()
        return incident

    def get_by_id(
        self,
        company_id: uuid.UUID,
        incident_id: uuid.UUID,
    ) -> AlertIncident | None:
        return (
            self.db.query(AlertIncident)
            .filter(
                AlertIncident.id == incident_id,
                AlertIncident.company_id == company_id,
            )
            .first()
        )

    def get_by_alert_id(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> AlertIncident | None:
        return (
            self.db.query(AlertIncident)
            .filter(
                AlertIncident.alert_id == alert_id,
                AlertIncident.company_id == company_id,
            )
            .first()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        priority: str | None = None,
        assigned_user_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AlertIncident], int]:
        query = self.db.query(AlertIncident).filter(
            AlertIncident.company_id == company_id,
        )

        if status is not None:
            query = query.filter(
                AlertIncident.status == status
            )

        if priority is not None:
            query = query.filter(
                AlertIncident.priority == priority
            )

        if assigned_user_id is not None:
            query = query.filter(
                AlertIncident.assigned_user_id
                == assigned_user_id
            )

        total = query.count()
        query = query.order_by(
            AlertIncident.created_at.desc()
        )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def update(
        self,
        incident: AlertIncident,
        **kwargs,
    ) -> AlertIncident:
        for key, value in kwargs.items():
            if value is not None:
                setattr(incident, key, value)
        incident.updated_at = datetime.utcnow()
        self.db.flush()
        return incident

    def resolve(
        self,
        company_id: uuid.UUID,
        incident_id: uuid.UUID,
    ) -> AlertIncident | None:
        incident = self.get_by_id(
            company_id, incident_id
        )
        if incident and incident.status in [
            "OPEN",
            "IN_PROGRESS",
        ]:
            incident.status = "RESOLVED"
            incident.resolved_at = datetime.utcnow()
            incident.updated_at = datetime.utcnow()
            self.db.flush()
        return incident

    def get_summary(
        self,
        company_id: uuid.UUID,
    ) -> dict:
        base = self.db.query(AlertIncident).filter(
            AlertIncident.company_id == company_id,
        )

        open_count = base.filter(
            AlertIncident.status == "OPEN"
        ).count()

        in_progress_count = base.filter(
            AlertIncident.status == "IN_PROGRESS"
        ).count()

        resolved_count = base.filter(
            AlertIncident.status == "RESOLVED"
        ).count()

        closed_count = base.filter(
            AlertIncident.status == "CLOSED"
        ).count()

        critical_count = base.filter(
            AlertIncident.priority == "CRITICAL",
            AlertIncident.status.in_(
                ["OPEN", "IN_PROGRESS"]
            ),
        ).count()

        avg_resolution = (
            self.db.query(
                func.avg(
                    func.extract(
                        "epoch",
                        AlertIncident.resolved_at
                        - AlertIncident.created_at,
                    )
                )
            )
            .filter(
                AlertIncident.company_id == company_id,
                AlertIncident.resolved_at.isnot(None),
            )
            .scalar()
        )

        avg_resolution_minutes = None
        if avg_resolution is not None:
            avg_resolution_minutes = round(
                float(avg_resolution) / 60.0, 2
            )

        return {
            "open_incidents": open_count,
            "in_progress_incidents": in_progress_count,
            "resolved_incidents": resolved_count,
            "closed_incidents": closed_count,
            "average_resolution_time_minutes": (
                avg_resolution_minutes
            ),
            "critical_incidents": critical_count,
        }
