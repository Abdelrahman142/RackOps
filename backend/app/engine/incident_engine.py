import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.incident import AlertIncident


class IncidentEngine:
    def __init__(self, db: Session):
        self.db = db

    def create_incident_from_alert(
        self,
        alert: Alert,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
    ) -> AlertIncident:
        if title is None:
            title = f"Incident: {alert.title}"

        if description is None:
            description = (
                f"Auto-created from alert "
                f"'{alert.title}'. "
                f"Severity: {alert.severity}. "
                f"Device: {alert.device_id}"
            )

        if priority is None:
            priority = (
                "CRITICAL"
                if alert.severity == "CRITICAL"
                else "HIGH"
                if alert.severity == "WARNING"
                else "LOW"
            )

        incident = AlertIncident(
            company_id=alert.company_id,
            alert_id=alert.id,
            title=title,
            description=description,
            priority=priority,
        )
        self.db.add(incident)
        self.db.flush()
        return incident

    def get_priority_for_severity(
        self,
        severity: str,
    ) -> str:
        mapping = {
            "CRITICAL": "CRITICAL",
            "WARNING": "HIGH",
            "INFO": "LOW",
        }
        return mapping.get(severity, "MEDIUM")

    def build_incident_description(
        self,
        alert_title: str,
        alert_severity: str,
        device_id: str,
        metric_key: str | None = None,
        value: float | None = None,
        threshold: float | None = None,
    ) -> str:
        parts = [
            f"Alert: {alert_title}",
            f"Severity: {alert_severity}",
            f"Device: {device_id}",
        ]

        if metric_key and value is not None:
            parts.append(
                f"Metric: {metric_key} = {value}"
            )

        if threshold is not None:
            parts.append(f"Threshold: {threshold}")

        return " | ".join(parts)
