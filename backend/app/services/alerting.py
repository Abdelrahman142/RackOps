import math
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.engine.alert_engine import AlertEngine
from app.engine.incident_engine import IncidentEngine
from app.repositories.alert import AlertRepository
from app.repositories.alert_rule import (
    AlertRuleRepository,
)
from app.repositories.incident import (
    IncidentRepository,
)
from app.repositories.maintenance_window import (
    MaintenanceWindowRepository,
)
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_CONDITIONS = {
    "GREATER_THAN",
    "LESS_THAN",
    "EQUAL",
    "NOT_EQUAL",
}

VALID_SEVERITIES = {"INFO", "WARNING", "CRITICAL"}

VALID_ALERT_STATUSES = {
    "OPEN",
    "ACKNOWLEDGED",
    "RESOLVED",
    "SUPPRESSED",
}

VALID_INCIDENT_STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
}

VALID_INCIDENT_PRIORITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

VALID_WINDOW_STATUSES = {
    "SCHEDULED",
    "ACTIVE",
    "COMPLETED",
    "CANCELLED",
}


class AlertingService:
    def __init__(self, db: Session):
        self.db = db
        self.rule_repo = AlertRuleRepository(db)
        self.alert_repo = AlertRepository(db)
        self.incident_repo = IncidentRepository(db)
        self.window_repo = MaintenanceWindowRepository(
            db
        )
        self.alert_engine = AlertEngine()
        self.incident_engine = IncidentEngine(db)

    # --- Alert Rule Methods ---

    def create_rule(
        self,
        company_id: uuid.UUID,
        name: str,
        metric_key: str,
        condition: str,
        threshold_value: float,
        severity: str = "WARNING",
        enabled: bool = True,
        evaluation_interval_seconds: int = 300,
        description: str | None = None,
    ) -> dict:
        if condition not in VALID_CONDITIONS:
            raise ValidationException(
                detail=(
                    f"Invalid condition: {condition}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_CONDITIONS))}"
                )
            )

        if severity not in VALID_SEVERITIES:
            raise ValidationException(
                detail=(
                    f"Invalid severity: {severity}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_SEVERITIES))}"
                )
            )

        rule = self.rule_repo.create(
            company_id=company_id,
            name=name,
            metric_key=metric_key,
            condition=condition,
            threshold_value=threshold_value,
            severity=severity,
            enabled=enabled,
            evaluation_interval_seconds=evaluation_interval_seconds,
            description=description,
        )

        self.db.commit()
        self.db.refresh(rule)

        return self._serialize_rule(rule)

    def get_rule(
        self,
        company_id: uuid.UUID,
        rule_id: uuid.UUID,
    ) -> dict:
        rule = self.rule_repo.get_by_id(
            company_id, rule_id
        )
        if not rule:
            raise NotFoundException(
                detail="Alert rule not found"
            )
        return self._serialize_rule(rule)

    def list_rules(
        self,
        company_id: uuid.UUID,
        severity: str | None = None,
        enabled: bool | None = None,
        metric_key: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if severity is not None:
            if severity not in VALID_SEVERITIES:
                raise ValidationException(
                    detail=(
                        f"Invalid severity filter: "
                        f"{severity}"
                    )
                )

        items, total = self.rule_repo.list_by_company(
            company_id=company_id,
            severity=severity,
            enabled=enabled,
            metric_key=metric_key,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "rules": [
                self._serialize_rule(r) for r in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_rule(
        self,
        company_id: uuid.UUID,
        rule_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        metric_key: str | None = None,
        condition: str | None = None,
        threshold_value: float | None = None,
        severity: str | None = None,
        enabled: bool | None = None,
        evaluation_interval_seconds: int | None = None,
    ) -> dict:
        rule = self.rule_repo.get_by_id(
            company_id, rule_id
        )
        if not rule:
            raise NotFoundException(
                detail="Alert rule not found"
            )

        if condition is not None:
            if condition not in VALID_CONDITIONS:
                raise ValidationException(
                    detail=f"Invalid condition: {condition}"
                )

        if severity is not None:
            if severity not in VALID_SEVERITIES:
                raise ValidationException(
                    detail=(
                        f"Invalid severity: {severity}"
                    )
                )

        self.rule_repo.update(
            rule,
            name=name,
            description=description,
            metric_key=metric_key,
            condition=condition,
            threshold_value=threshold_value,
            severity=severity,
            enabled=enabled,
            evaluation_interval_seconds=evaluation_interval_seconds,
        )

        self.db.commit()
        self.db.refresh(rule)

        return self._serialize_rule(rule)

    def delete_rule(
        self,
        company_id: uuid.UUID,
        rule_id: uuid.UUID,
    ) -> dict:
        rule = self.rule_repo.get_by_id(
            company_id, rule_id
        )
        if not rule:
            raise NotFoundException(
                detail="Alert rule not found"
            )

        self.rule_repo.soft_delete(rule)
        self.db.commit()

        return {
            "message": (
                "Alert rule deleted successfully"
            )
        }

    # --- Alert Methods ---

    def get_alert(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> dict:
        alert = self.alert_repo.get_by_id(
            company_id, alert_id
        )
        if not alert:
            raise NotFoundException(
                detail="Alert not found"
            )
        return self._serialize_alert(alert)

    def list_alerts(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        severity: str | None = None,
        device_id: uuid.UUID | None = None,
        rule_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_ALERT_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        if severity is not None:
            if severity not in VALID_SEVERITIES:
                raise ValidationException(
                    detail=(
                        f"Invalid severity: {severity}"
                    )
                )

        items, total = self.alert_repo.list_by_company(
            company_id=company_id,
            status=status,
            severity=severity,
            device_id=device_id,
            rule_id=rule_id,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "alerts": [
                self._serialize_alert(a) for a in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def acknowledge_alert(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> dict:
        alert = self.alert_repo.acknowledge(
            company_id, alert_id
        )
        if not alert:
            raise NotFoundException(
                detail="Alert not found or already processed"
            )

        self.db.commit()
        self.db.refresh(alert)

        return self._serialize_alert(alert)

    def resolve_alert(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
    ) -> dict:
        alert = self.alert_repo.resolve(
            company_id, alert_id
        )
        if not alert:
            raise NotFoundException(
                detail="Alert not found or already resolved"
            )

        self.db.commit()
        self.db.refresh(alert)

        return self._serialize_alert(alert)

    def get_alert_summary(
        self,
        company_id: uuid.UUID,
    ) -> dict:
        return self.alert_repo.get_summary(company_id)

    # --- Incident Methods ---

    def create_incident(
        self,
        company_id: uuid.UUID,
        alert_id: uuid.UUID,
        title: str,
        description: str | None = None,
        priority: str = "MEDIUM",
        assigned_user_id: uuid.UUID | None = None,
    ) -> dict:
        if priority not in VALID_INCIDENT_PRIORITIES:
            raise ValidationException(
                detail=(
                    f"Invalid priority: {priority}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_INCIDENT_PRIORITIES))}"
                )
            )

        alert = self.alert_repo.get_by_id(
            company_id, alert_id
        )
        if not alert:
            raise NotFoundException(
                detail="Alert not found"
            )

        existing = self.incident_repo.get_by_alert_id(
            company_id, alert_id
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "An incident already exists for "
                    "this alert"
                )
            )

        incident = self.incident_repo.create(
            company_id=company_id,
            alert_id=alert_id,
            title=title,
            description=description,
            priority=priority,
            assigned_user_id=assigned_user_id,
        )

        self.db.commit()
        self.db.refresh(incident)

        return self._serialize_incident(incident)

    def get_incident(
        self,
        company_id: uuid.UUID,
        incident_id: uuid.UUID,
    ) -> dict:
        incident = self.incident_repo.get_by_id(
            company_id, incident_id
        )
        if not incident:
            raise NotFoundException(
                detail="Incident not found"
            )
        return self._serialize_incident(incident)

    def list_incidents(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        priority: str | None = None,
        assigned_user_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_INCIDENT_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        if priority is not None:
            if priority not in VALID_INCIDENT_PRIORITIES:
                raise ValidationException(
                    detail=(
                        f"Invalid priority: {priority}"
                    )
                )

        items, total = (
            self.incident_repo.list_by_company(
                company_id=company_id,
                status=status,
                priority=priority,
                assigned_user_id=assigned_user_id,
                page=page,
                size=size,
            )
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "incidents": [
                self._serialize_incident(i)
                for i in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_incident(
        self,
        company_id: uuid.UUID,
        incident_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        assigned_user_id: str | None = None,
    ) -> dict:
        incident = self.incident_repo.get_by_id(
            company_id, incident_id
        )
        if not incident:
            raise NotFoundException(
                detail="Incident not found"
            )

        if status is not None:
            if status not in VALID_INCIDENT_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        if priority is not None:
            if priority not in VALID_INCIDENT_PRIORITIES:
                raise ValidationException(
                    detail=(
                        f"Invalid priority: {priority}"
                    )
                )

        parsed_user_id = None
        if assigned_user_id is not None:
            parsed_user_id = uuid.UUID(
                assigned_user_id
            )

        self.incident_repo.update(
            incident,
            title=title,
            description=description,
            priority=priority,
            status=status,
            assigned_user_id=parsed_user_id,
        )

        self.db.commit()
        self.db.refresh(incident)

        return self._serialize_incident(incident)

    def resolve_incident(
        self,
        company_id: uuid.UUID,
        incident_id: uuid.UUID,
    ) -> dict:
        incident = self.incident_repo.resolve(
            company_id, incident_id
        )
        if not incident:
            raise NotFoundException(
                detail=(
                    "Incident not found or already resolved"
                )
            )

        self.db.commit()
        self.db.refresh(incident)

        return self._serialize_incident(incident)

    def get_incident_summary(
        self,
        company_id: uuid.UUID,
    ) -> dict:
        return self.incident_repo.get_summary(company_id)

    # --- Maintenance Window Methods ---

    def create_window(
        self,
        company_id: uuid.UUID,
        name: str,
        start_time: datetime,
        end_time: datetime,
        created_by: uuid.UUID,
        description: str | None = None,
    ) -> dict:
        if end_time <= start_time:
            raise ValidationException(
                detail=(
                    "End time must be after start time"
                )
            )

        window = self.window_repo.create(
            company_id=company_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            created_by=created_by,
            description=description,
        )

        self.db.commit()
        self.db.refresh(window)

        return self._serialize_window(window)

    def get_window(
        self,
        company_id: uuid.UUID,
        window_id: uuid.UUID,
    ) -> dict:
        window = self.window_repo.get_by_id(
            company_id, window_id
        )
        if not window:
            raise NotFoundException(
                detail="Maintenance window not found"
            )
        return self._serialize_window(window)

    def list_windows(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_WINDOW_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        items, total = (
            self.window_repo.list_by_company(
                company_id=company_id,
                status=status,
                page=page,
                size=size,
            )
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "windows": [
                self._serialize_window(w)
                for w in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_window(
        self,
        company_id: uuid.UUID,
        window_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        status: str | None = None,
    ) -> dict:
        window = self.window_repo.get_by_id(
            company_id, window_id
        )
        if not window:
            raise NotFoundException(
                detail="Maintenance window not found"
            )

        if status is not None:
            if status not in VALID_WINDOW_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        self.window_repo.update(
            window,
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )

        self.db.commit()
        self.db.refresh(window)

        return self._serialize_window(window)

    def delete_window(
        self,
        company_id: uuid.UUID,
        window_id: uuid.UUID,
    ) -> dict:
        window = self.window_repo.get_by_id(
            company_id, window_id
        )
        if not window:
            raise NotFoundException(
                detail="Maintenance window not found"
            )

        self.window_repo.delete(company_id, window_id)
        self.db.commit()

        return {
            "message": (
                "Maintenance window deleted successfully"
            )
        }

    # --- Evaluation Engine Methods ---

    def evaluate_all_rules(self) -> list[dict]:
        from app.models.monitoring_target import (
            MonitoringTarget,
        )
        from app.repositories.metric_data import (
            MetricDataRepository,
        )

        metric_repo = MetricDataRepository(self.db)
        results = []

        targets = (
            self.db.query(MonitoringTarget)
            .filter(
                MonitoringTarget.enabled.is_(True),
            )
            .all()
        )

        for target in targets:
            company_id = target.company_id
            device_id = target.device_id

            if self.window_repo.has_active_window(
                company_id
            ):
                continue

            rules = (
                self.rule_repo.list_enabled_by_company(
                    company_id
                )
            )

            latest_metrics = (
                metric_repo.get_latest_by_device(
                    company_id, device_id
                )
            )

            for metric_data in latest_metrics:
                from app.models.metric_definition import (
                    MetricDefinition,
                )

                defn = (
                    self.db.query(MetricDefinition)
                    .filter(
                        MetricDefinition.id
                        == metric_data.metric_definition_id
                    )
                    .first()
                )

                if not defn:
                    continue

                eval_results = (
                    self.alert_engine.evaluate_rules_for_metric(  # noqa: E501
                        rules=rules,
                        metric_key=defn.metric_key,
                        value=metric_data.value,
                        device_id=str(device_id),
                    )
                )

                for eval_result in eval_results:
                    rule_id = uuid.UUID(
                        eval_result.rule_id
                    )

                    has_open = (
                        self.rule_repo.has_open_alert_for_device(  # noqa: E501
                            company_id,
                            rule_id,
                            device_id,
                        )
                    )

                    if has_open:
                        continue

                    title = (
                        self.alert_engine.build_alert_title(  # noqa: E501
                            rule_name=next(
                                (
                                    r.name
                                    for r in rules
                                    if str(r.id)
                                    == eval_result.rule_id
                                ),
                                "Unknown",
                            ),
                            device_id=str(device_id),
                            value=eval_result.value,
                            condition=eval_result.condition,
                            threshold=eval_result.threshold,
                        )
                    )

                    description = (
                        self.alert_engine.build_alert_description(  # noqa: E501
                            metric_key=eval_result.metric_key,
                            value=eval_result.value,
                            condition=eval_result.condition,
                            threshold=eval_result.threshold,
                            severity=eval_result.severity,
                        )
                    )

                    alert = self.alert_repo.create(
                        company_id=company_id,
                        device_id=device_id,
                        rule_id=rule_id,
                        title=title,
                        severity=eval_result.severity,
                        description=description,
                    )

                    results.append({
                        "alert_id": str(alert.id),
                        "rule_id": eval_result.rule_id,
                        "device_id": str(device_id),
                        "severity": eval_result.severity,
                    })

        if results:
            self.db.commit()

        return results

    def create_incidents_for_critical_alerts(
        self,
    ) -> list[dict]:
        from app.models.alert import Alert
        from app.models.company import Company

        companies = (
            self.db.query(Company).all()
        )

        results = []

        for company in companies:
            company_id = company.id

            if self.window_repo.has_active_window(
                company_id
            ):
                continue

            open_critical = (
                self.db.query(Alert)
                .filter(
                    Alert.company_id == company_id,
                    Alert.severity == "CRITICAL",
                    Alert.status.in_(
                        ["OPEN", "ACKNOWLEDGED"]
                    ),
                )
                .all()
            )

            for alert in open_critical:
                existing = (
                    self.incident_repo.get_by_alert_id(
                        company_id, alert.id
                    )
                )

                if existing:
                    continue

                incident = (
                    self.incident_engine.create_incident_from_alert(  # noqa: E501
                        alert
                    )
                )

                results.append({
                    "incident_id": str(incident.id),
                    "alert_id": str(alert.id),
                    "company_id": str(company_id),
                })

        if results:
            self.db.commit()

        return results

    def activate_scheduled_windows(self) -> list[dict]:
        now = datetime.utcnow()
        updated = []

        from app.models.maintenance_window import (
            MaintenanceWindow,
        )

        scheduled = (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.status
                == "SCHEDULED",
                MaintenanceWindow.start_time <= now,
                MaintenanceWindow.end_time >= now,
            )
            .all()
        )

        for window in scheduled:
            window.status = "ACTIVE"
            updated.append(str(window.id))

        completed = (
            self.db.query(MaintenanceWindow)
            .filter(
                MaintenanceWindow.status.in_(
                    ["SCHEDULED", "ACTIVE"]
                ),
                MaintenanceWindow.end_time < now,
            )
            .all()
        )

        for window in completed:
            window.status = "COMPLETED"
            if str(window.id) not in updated:
                updated.append(str(window.id))

        if updated:
            self.db.commit()

        return updated

    # --- Serialization ---

    def _serialize_rule(self, rule) -> dict:
        return {
            "id": str(rule.id),
            "company_id": str(rule.company_id),
            "name": rule.name,
            "description": rule.description,
            "metric_key": rule.metric_key,
            "condition": rule.condition,
            "threshold_value": rule.threshold_value,
            "severity": rule.severity,
            "enabled": rule.enabled,
            "evaluation_interval_seconds": (
                rule.evaluation_interval_seconds
            ),
            "created_at": rule.created_at.isoformat(),
            "updated_at": rule.updated_at.isoformat(),
        }

    def _serialize_alert(self, alert) -> dict:
        return {
            "id": str(alert.id),
            "company_id": str(alert.company_id),
            "device_id": str(alert.device_id),
            "rule_id": str(alert.rule_id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "triggered_at": (
                alert.triggered_at.isoformat()
            ),
            "resolved_at": (
                alert.resolved_at.isoformat()
                if alert.resolved_at
                else None
            ),
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
        }

    def _serialize_incident(self, incident) -> dict:
        return {
            "id": str(incident.id),
            "company_id": str(incident.company_id),
            "alert_id": str(incident.alert_id),
            "title": incident.title,
            "description": incident.description,
            "priority": incident.priority,
            "status": incident.status,
            "assigned_user_id": (
                str(incident.assigned_user_id)
                if incident.assigned_user_id
                else None
            ),
            "created_at": (
                incident.created_at.isoformat()
            ),
            "updated_at": (
                incident.updated_at.isoformat()
            ),
            "resolved_at": (
                incident.resolved_at.isoformat()
                if incident.resolved_at
                else None
            ),
        }

    def _serialize_window(self, window) -> dict:
        return {
            "id": str(window.id),
            "company_id": str(window.company_id),
            "name": window.name,
            "description": window.description,
            "start_time": (
                window.start_time.isoformat()
            ),
            "end_time": window.end_time.isoformat(),
            "created_by": str(window.created_by),
            "status": window.status,
            "created_at": (
                window.created_at.isoformat()
            ),
        }
