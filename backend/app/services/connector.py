import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.engine.automation_engine import AutomationEngine
from app.repositories.device_connector import (
    DeviceConnectorRepository,
)
from app.utils.exceptions import (
    NotFoundException,
    ValidationException,
)

VALID_CONNECTOR_TYPES = {"SSH", "SNMP", "API", "ANSIBLE"}


class ConnectorService:
    def __init__(self, db: Session):
        self.db = db
        self.connector_repo = DeviceConnectorRepository(db)
        self.engine = AutomationEngine(db)

    def create_connector(
        self,
        device_id: uuid.UUID,
        company_id: uuid.UUID,
        connector_type: str,
        hostname: str,
        username: str,
        port: int = 22,
        password: str | None = None,
        enabled: bool = True,
    ) -> dict:
        if connector_type not in VALID_CONNECTOR_TYPES:
            raise ValidationException(
                detail=f"Invalid connector type: {connector_type}. Valid: {', '.join(VALID_CONNECTOR_TYPES)}"
            )

        encrypted_password = None
        if password:
            encrypted_password = self._encrypt_password(
                password
            )

        connector = self.connector_repo.create(
            device_id=device_id,
            company_id=company_id,
            connector_type=connector_type,
            hostname=hostname,
            port=port,
            username=username,
            encrypted_password=encrypted_password,
            enabled=enabled,
        )
        self.db.commit()
        self.db.refresh(connector)
        return self._serialize_connector(connector)

    def get_connector(
        self,
        company_id: uuid.UUID,
        connector_id: uuid.UUID,
    ):
        connector = self.connector_repo.get_by_id(
            company_id, connector_id
        )
        if connector is None:
            raise NotFoundException(
                detail="Connector not found"
            )
        return connector

    def get_connector_response(
        self,
        company_id: uuid.UUID,
        connector_id: uuid.UUID,
    ) -> dict:
        connector = self.get_connector(company_id, connector_id)
        return self._serialize_connector(connector)

    def list_connectors_for_device(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> list[dict]:
        connectors = self.connector_repo.get_by_device_id(
            company_id, device_id
        )
        return [self._serialize_connector(c) for c in connectors]

    def test_connector(
        self,
        company_id: uuid.UUID,
        connector_id: uuid.UUID,
    ):
        connector = self.get_connector(company_id, connector_id)
        result = self.engine.test_connector(connector)
        return {
            "connector_id": str(connector.id),
            "success": result.success,
            "message": result.output
            if result.success
            else result.error_message,
            "tested_at": datetime.utcnow().isoformat(),
        }

    def _serialize_connector(self, connector) -> dict:
        return {
            "id": str(connector.id),
            "device_id": str(connector.device_id),
            "company_id": str(connector.company_id),
            "connector_type": connector.connector_type,
            "hostname": connector.hostname,
            "port": connector.port,
            "username": connector.username,
            "enabled": connector.enabled,
            "last_connection_test": (
                connector.last_connection_test.isoformat()
                if connector.last_connection_test
                else None
            ),
            "created_at": connector.created_at.isoformat(),
            "updated_at": connector.updated_at.isoformat(),
        }

    def _encrypt_password(self, password: str) -> str:
        import base64

        return base64.b64encode(password.encode()).decode()
