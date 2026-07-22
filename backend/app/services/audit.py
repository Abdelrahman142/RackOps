import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.audit_log import AuditLogRepository


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.log_repo = AuditLogRepository(db)

    def log(
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
    ) -> None:
        self.log_repo.create(
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
        self.db.commit()

    def get_log(
        self,
        company_id: uuid.UUID,
        log_id: uuid.UUID,
    ):
        log = self.log_repo.get_by_id(company_id, log_id)
        if log is None:
            return None
        return self._serialize_log(log)

    def list_logs(
        self,
        company_id: uuid.UUID,
        action: str | None = None,
        resource: str | None = None,
        user_id: uuid.UUID | None = None,
        device_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict], int]:
        items, total = self.log_repo.list_logs(
            company_id, action, resource, user_id, device_id, page, size
        )
        return [self._serialize_log(l) for l in items], total

    def _serialize_log(self, log) -> dict:
        return {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "company_id": str(log.company_id),
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "device_id": str(log.device_id) if log.device_id else None,
            "details": log.details,
            "status": log.status,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
