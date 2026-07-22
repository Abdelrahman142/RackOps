import uuid

from sqlalchemy.orm import Session

from app.models.device_connector import DeviceConnector


class DeviceConnectorRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        device_id: uuid.UUID,
        company_id: uuid.UUID,
        connector_type: str,
        hostname: str,
        username: str,
        port: int = 22,
        encrypted_password: str | None = None,
        enabled: bool = True,
    ) -> DeviceConnector:
        connector = DeviceConnector(
            device_id=device_id,
            company_id=company_id,
            connector_type=connector_type,
            hostname=hostname,
            port=port,
            username=username,
            encrypted_password=encrypted_password,
            enabled=enabled,
        )
        self.db.add(connector)
        self.db.flush()
        return connector

    def get_by_id(
        self,
        company_id: uuid.UUID,
        connector_id: uuid.UUID,
    ) -> DeviceConnector | None:
        return (
            self.db.query(DeviceConnector)
            .filter(
                DeviceConnector.id == connector_id,
                DeviceConnector.company_id == company_id,
            )
            .first()
        )

    def get_by_device_id(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> list[DeviceConnector]:
        return (
            self.db.query(DeviceConnector)
            .filter(
                DeviceConnector.device_id == device_id,
                DeviceConnector.company_id == company_id,
            )
            .all()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        connector_type: str | None = None,
    ) -> list[DeviceConnector]:
        query = (
            self.db.query(DeviceConnector)
            .filter(
                DeviceConnector.company_id == company_id,
            )
        )
        if connector_type:
            query = query.filter(
                DeviceConnector.connector_type == connector_type
            )
        return query.all()

    def update_last_connection_test(
        self,
        connector: DeviceConnector,
        tested_at,
    ) -> DeviceConnector:
        connector.last_connection_test = tested_at
        self.db.flush()
        return connector
