import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.physical_connection import (
    PhysicalConnection,
)


class PhysicalConnectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        source_interface_id: uuid.UUID,
        destination_interface_id: uuid.UUID,
        connection_type: str = "COPPER",
        cable_type: str | None = None,
        length_meters: int | None = None,
        status: str = "ACTIVE",
    ) -> PhysicalConnection:
        connection = PhysicalConnection(
            company_id=company_id,
            source_interface_id=source_interface_id,
            destination_interface_id=(
                destination_interface_id
            ),
            connection_type=connection_type,
            cable_type=cable_type,
            length_meters=length_meters,
            status=status,
        )
        self.db.add(connection)
        self.db.flush()
        return connection

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> PhysicalConnection | None:
        return (
            self.db.query(PhysicalConnection)
            .filter(
                PhysicalConnection.id == connection_id,
                PhysicalConnection.company_id
                == company_id,
                PhysicalConnection.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_interfaces(
        self,
        source_interface_id: uuid.UUID,
        destination_interface_id: uuid.UUID,
    ) -> PhysicalConnection | None:
        return (
            self.db.query(PhysicalConnection)
            .filter(
                PhysicalConnection.source_interface_id
                == source_interface_id,
                PhysicalConnection.destination_interface_id
                == destination_interface_id,
                PhysicalConnection.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_interface(
        self,
        interface_id: uuid.UUID,
    ) -> PhysicalConnection | None:
        return (
            self.db.query(PhysicalConnection)
            .filter(
                (
                    PhysicalConnection.source_interface_id
                    == interface_id
                )
                | (
                    PhysicalConnection.destination_interface_id
                    == interface_id
                ),
                PhysicalConnection.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_company(
        self,
        company_id: uuid.UUID,
        status: str | None = None,
        connection_type: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[PhysicalConnection], int]:
        query = self.db.query(
            PhysicalConnection
        ).filter(
            PhysicalConnection.company_id == company_id,
            PhysicalConnection.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(
                PhysicalConnection.status == status
            )

        if connection_type is not None:
            query = query.filter(
                PhysicalConnection.connection_type
                == connection_type
            )

        total = query.count()

        sort_column = getattr(
            PhysicalConnection,
            sort_by,
            PhysicalConnection.created_at,
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_all_by_company(
        self,
        company_id: uuid.UUID,
    ) -> list[PhysicalConnection]:
        return (
            self.db.query(PhysicalConnection)
            .filter(
                PhysicalConnection.company_id
                == company_id,
                PhysicalConnection.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        connection: PhysicalConnection,
        connection_type: str | None = None,
        cable_type: str | None = None,
        length_meters: int | None = None,
        status: str | None = None,
    ) -> PhysicalConnection:
        if connection_type is not None:
            connection.connection_type = connection_type
        if cable_type is not None:
            connection.cable_type = cable_type
        if length_meters is not None:
            connection.length_meters = length_meters
        if status is not None:
            connection.status = status
        self.db.flush()
        return connection

    def soft_delete(
        self,
        connection: PhysicalConnection,
    ) -> PhysicalConnection:
        connection.deleted_at = datetime.utcnow()
        self.db.flush()
        return connection
