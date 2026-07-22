import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        action: str,
        resource: str,
        resource_id: str | None = None,
        device_id: uuid.UUID | None = None,
        details: str | None = None,
        status: str = "SUCCESS",
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            company_id=company_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            device_id=device_id,
            details=details,
            status=status,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def get_by_id(
        self,
        company_id: uuid.UUID,
        log_id: uuid.UUID,
    ) -> AuditLog | None:
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.id == log_id,
                AuditLog.company_id == company_id,
            )
            .first()
        )

    def list_logs(
        self,
        company_id: uuid.UUID,
        action: str | None = None,
        resource: str | None = None,
        user_id: uuid.UUID | None = None,
        device_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        query = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.company_id == company_id,
            )
        )
        if action:
            query = query.filter(AuditLog.action == action)
        if resource:
            query = query.filter(AuditLog.resource == resource)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if device_id:
            query = query.filter(AuditLog.device_id == device_id)

        total = query.count()
        items = (
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total
