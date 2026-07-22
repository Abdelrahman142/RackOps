import uuid

from sqlalchemy.orm import Session

from app.models.configuration_backup import (
    ConfigurationBackup,
)


class ConfigurationBackupRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        device_id: uuid.UUID,
        company_id: uuid.UUID,
        backup_type: str,
        location: str,
        created_by: uuid.UUID,
        size: float | None = None,
        checksum: str | None = None,
    ) -> ConfigurationBackup:
        backup = ConfigurationBackup(
            device_id=device_id,
            company_id=company_id,
            backup_type=backup_type,
            location=location,
            size=size,
            checksum=checksum,
            status="PENDING",
            created_by=created_by,
        )
        self.db.add(backup)
        self.db.flush()
        return backup

    def get_by_id(
        self,
        company_id: uuid.UUID,
        backup_id: uuid.UUID,
    ) -> ConfigurationBackup | None:
        return (
            self.db.query(ConfigurationBackup)
            .filter(
                ConfigurationBackup.id == backup_id,
                ConfigurationBackup.company_id == company_id,
            )
            .first()
        )

    def list_by_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> list[ConfigurationBackup]:
        return (
            self.db.query(ConfigurationBackup)
            .filter(
                ConfigurationBackup.device_id == device_id,
                ConfigurationBackup.company_id == company_id,
            )
            .order_by(ConfigurationBackup.created_at.desc())
            .all()
        )

    def update_status(
        self,
        backup: ConfigurationBackup,
        status: str,
        size: float | None = None,
        checksum: str | None = None,
    ) -> ConfigurationBackup:
        backup.status = status
        if size is not None:
            backup.size = size
        if checksum is not None:
            backup.checksum = checksum
        self.db.flush()
        return backup
