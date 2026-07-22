import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        rule_id: uuid.UUID,
        title: str,
        severity: str,
        description: str | None = None,
        triggered_at: datetime | None = None,
    ) -> Alert:
        if triggered_at is None:
            triggered_at = datetime.utcnow()

        alert = Alert(
            company_id=company_id,
            device_id=device_id,
            rule_id=rule_id,
            title=title,
            severity=severity,
            description=description,
            triggered_at=triggered_at,
        )
        self.db.add(alert)
        self.db.flush()
        return alert

    def get_by_id(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> Alert | None:
        return (
            self.db.query(Alert)
            .filter(
                Alert.id == alert_id,
                Alert.company_id == company_id,
            )
            .first()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        severity: str | None = None,
        device_id: uuid.UUID | None = None,
        rule_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Alert], int]:
        query = self.db.query(Alert).filter(
            Alert.company_id == company_id,
        )

        if status is not None:
            query = query.filter(Alert.status == status)

        if severity is not None:
            query = query.filter(
                Alert.severity == severity
            )

        if device_id is not None:
            query = query.filter(
                Alert.device_id == device_id
            )

        if rule_id is not None:
            query = query.filter(
                Alert.rule_id == rule_id
            )

        total = query.count()
        query = query.order_by(
            Alert.triggered_at.desc()
        )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def get_summary(
        self,
        company_id: uuid.UUID,
    ) -> dict:
        base = self.db.query(Alert).filter(
            Alert.company_id == company_id,
        )

        total = base.count()

        open_count = base.filter(
            Alert.status.in_(["OPEN", "ACKNOWLEDGED"])
        ).count()

        critical_count = base.filter(
            Alert.severity == "CRITICAL",
            Alert.status.in_(["OPEN", "ACKNOWLEDGED"]),
        ).count()

        warning_count = base.filter(
            Alert.severity == "WARNING",
            Alert.status.in_(["OPEN", "ACKNOWLEDGED"]),
        ).count()

        info_count = base.filter(
            Alert.severity == "INFO",
            Alert.status.in_(["OPEN", "ACKNOWLEDGED"]),
        ).count()

        return {
            "total_alerts": total,
            "open_alerts": open_count,
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "info_alerts": info_count,
        }

    def acknowledge(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> Alert | None:
        alert = self.get_by_id(company_id, alert_id)
        if alert and alert.status == "OPEN":
            alert.status = "ACKNOWLEDGED"
            alert.updated_at = datetime.utcnow()
            self.db.flush()
        return alert

    def resolve(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> Alert | None:
        alert = self.get_by_id(company_id, alert_id)
        if alert and alert.status in [
            "OPEN",
            "ACKNOWLEDGED",
        ]:
            alert.status = "RESOLVED"
            alert.resolved_at = datetime.utcnow()
            alert.updated_at = datetime.utcnow()
            self.db.flush()
        return alert

    def suppress(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> Alert | None:
        alert = self.get_by_id(company_id, alert_id)
        if alert and alert.status in [
            "OPEN",
            "ACKNOWLEDGED",
        ]:
            alert.status = "SUPPRESSED"
            alert.updated_at = datetime.utcnow()
            self.db.flush()
        return alert

    def count_open_by_severity(
        self,
        company_id: uuid.UUID,
    ) -> dict[str, int]:
        results = (
            self.db.query(
                Alert.severity,
                func.count(Alert.id),
            )
            .filter(
                Alert.company_id == company_id,
                Alert.status.in_(
                    ["OPEN", "ACKNOWLEDGED"]
                ),
            )
            .group_by(Alert.severity)
            .all()
        )
        return {sev: count for sev, count in results}
