import uuid
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.alert_rule import AlertRule


class AlertRuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
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
    ) -> AlertRule:
        rule = AlertRule(
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
        self.db.add(rule)
        self.db.flush()
        return rule

    def get_by_id(
        self,
        company_id: uuid.UUID,
        rule_id: uuid.UUID,
    ) -> AlertRule | None:
        return (
            self.db.query(AlertRule)
            .filter(
                AlertRule.id == rule_id,
                AlertRule.company_id == company_id,
                AlertRule.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        severity: str | None = None,
        enabled: bool | None = None,
        metric_key: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AlertRule], int]:
        query = self.db.query(AlertRule).filter(
            AlertRule.company_id == company_id,
            AlertRule.deleted_at.is_(None),
        )

        if severity is not None:
            query = query.filter(
                AlertRule.severity == severity
            )

        if enabled is not None:
            query = query.filter(
                AlertRule.enabled == enabled
            )

        if metric_key is not None:
            query = query.filter(
                AlertRule.metric_key == metric_key
            )

        total = query.count()
        query = query.order_by(
            AlertRule.created_at.desc()
        )

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_enabled_by_company(
        self,
        company_id: uuid.UUID,
    ) -> list[AlertRule]:
        return (
            self.db.query(AlertRule)
            .filter(
                AlertRule.company_id == company_id,
                AlertRule.enabled.is_(True),
                AlertRule.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        rule: AlertRule,
        **kwargs,
    ) -> AlertRule:
        for key, value in kwargs.items():
            if value is not None:
                setattr(rule, key, value)
        rule.updated_at = datetime.utcnow()
        self.db.flush()
        return rule

    def soft_delete(self, rule: AlertRule) -> None:
        rule.deleted_at = datetime.utcnow()
        self.db.flush()

    def has_open_alert_for_device(
        self,
        company_id: uuid.UUID,
        rule_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> bool:
        from app.models.alert import Alert

        return (
            self.db.query(Alert)
            .filter(
                Alert.company_id == company_id,
                Alert.rule_id == rule_id,
                Alert.device_id == device_id,
                Alert.status.in_(
                    ["OPEN", "ACKNOWLEDGED"]
                ),
            )
            .first()
            is not None
        )
