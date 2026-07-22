import hashlib
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.configuration_backup import (
    ConfigurationBackupRepository,
)
from app.utils.exceptions import (
    NotFoundException,
    ValidationException,
)

VALID_BACKUP_TYPES = {"FULL", "CONFIG", "DATABASE"}


class BackupService:
    def __init__(self, db: Session):
        self.db = db
        self.backup_repo = ConfigurationBackupRepository(db)

    def create_backup(
        self,
        device_id: uuid.UUID,
        company_id: uuid.UUID,
        backup_type: str,
        created_by: uuid.UUID,
    ) -> dict:
        if backup_type not in VALID_BACKUP_TYPES:
            raise ValidationException(
                detail=f"Invalid backup type: {backup_type}. Valid: {', '.join(VALID_BACKUP_TYPES)}"
            )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        location = f"/backups/{device_id}/{backup_type}_{timestamp}"

        checksum = hashlib.sha256(
            f"{device_id}:{backup_type}:{timestamp}".encode()
        ).hexdigest()

        backup = self.backup_repo.create(
            device_id=device_id,
            company_id=company_id,
            backup_type=backup_type,
            location=location,
            created_by=created_by,
            checksum=checksum,
        )

        self.backup_repo.update_status(
            backup,
            "COMPLETED",
            size=0.0,
            checksum=checksum,
        )
        self.db.commit()
        self.db.refresh(backup)
        return self._serialize_backup(backup)

    def get_backup(
        self,
        company_id: uuid.UUID,
        backup_id: uuid.UUID,
    ):
        backup = self.backup_repo.get_by_id(
            company_id, backup_id
        )
        if backup is None:
            raise NotFoundException(
                detail="Backup not found"
            )
        return backup

    def list_backups_for_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> list[dict]:
        backups = self.backup_repo.list_by_device(
            company_id, device_id
        )
        return [self._serialize_backup(b) for b in backups]

    def _serialize_backup(self, backup) -> dict:
        return {
            "id": str(backup.id),
            "device_id": str(backup.device_id),
            "company_id": str(backup.company_id),
            "backup_type": backup.backup_type,
            "location": backup.location,
            "size": backup.size,
            "checksum": backup.checksum,
            "status": backup.status,
            "created_by": str(backup.created_by),
            "created_at": backup.created_at.isoformat(),
        }
