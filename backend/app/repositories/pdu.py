import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.pdu import PDU


class PDURepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        total_capacity_amp: float,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str = "ACTIVE",
        rack_id: uuid.UUID | None = None,
        current_usage_amp: float = 0,
        phase_type: str = "SINGLE",
    ) -> PDU:
        pdu = PDU(
            company_id=company_id,
            room_id=room_id,
            name=name,
            total_capacity_amp=total_capacity_amp,
            model=model,
            manufacturer=manufacturer,
            serial_number=serial_number,
            status=status,
            rack_id=rack_id,
            current_usage_amp=current_usage_amp,
            phase_type=phase_type,
        )
        self.db.add(pdu)
        self.db.flush()
        return pdu

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        pdu_id: uuid.UUID,
    ) -> PDU | None:
        return (
            self.db.query(PDU)
            .filter(
                PDU.id == pdu_id,
                PDU.company_id == company_id,
                PDU.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_room_and_name(
        self,
        room_id: uuid.UUID,
        name: str,
    ) -> PDU | None:
        return (
            self.db.query(PDU)
            .filter(
                PDU.room_id == room_id,
                PDU.name == name,
                PDU.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_serial_number(
        self,
        serial_number: str,
    ) -> PDU | None:
        return (
            self.db.query(PDU)
            .filter(
                PDU.serial_number == serial_number,
                PDU.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_room(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[PDU], int]:
        query = self.db.query(PDU).filter(
            PDU.company_id == company_id,
            PDU.room_id == room_id,
            PDU.deleted_at.is_(None),
        )

        if status is not None:
            query = query.filter(PDU.status == status)

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                PDU.name.ilike(search_pattern)
            )

        total = query.count()

        sort_column = getattr(
            PDU, sort_by, PDU.created_at
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def list_all_by_room(
        self,
        room_id: uuid.UUID,
    ) -> list[PDU]:
        return (
            self.db.query(PDU)
            .filter(
                PDU.room_id == room_id,
                PDU.deleted_at.is_(None),
            )
            .all()
        )

    def list_by_rack(
        self,
        rack_id: uuid.UUID,
    ) -> list[PDU]:
        return (
            self.db.query(PDU)
            .filter(
                PDU.rack_id == rack_id,
                PDU.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        pdu: PDU,
        name: str | None = None,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str | None = None,
        rack_id: uuid.UUID | None = None,
        total_capacity_amp: float | None = None,
        current_usage_amp: float | None = None,
        phase_type: str | None = None,
    ) -> PDU:
        if name is not None:
            pdu.name = name
        if model is not None:
            pdu.model = model
        if manufacturer is not None:
            pdu.manufacturer = manufacturer
        if serial_number is not None:
            pdu.serial_number = serial_number
        if status is not None:
            pdu.status = status
        if rack_id is not None:
            pdu.rack_id = rack_id
        if total_capacity_amp is not None:
            pdu.total_capacity_amp = total_capacity_amp
        if current_usage_amp is not None:
            pdu.current_usage_amp = current_usage_amp
        if phase_type is not None:
            pdu.phase_type = phase_type
        self.db.flush()
        return pdu

    def soft_delete(self, pdu: PDU) -> PDU:
        pdu.deleted_at = datetime.utcnow()
        self.db.flush()
        return pdu
