import math
import uuid

from sqlalchemy.orm import Session

from app.repositories.device import DeviceRepository
from app.repositories.pdu import PDURepository
from app.repositories.power_feed import PowerFeedRepository
from app.repositories.rack import RackRepository
from app.repositories.room import RoomRepository
from app.repositories.ups import UPSRepository
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_POWER_STATUSES = {
    "ACTIVE",
    "WARNING",
    "FAILED",
    "MAINTENANCE",
    "OFFLINE",
}

VALID_PHASE_TYPES = {"SINGLE", "THREE_PHASE"}

VALID_FEED_SOURCE_TYPES = {"UPS", "MAINS"}

VALID_FEED_DESTINATION_TYPES = {"PDU", "RACK"}


class PowerService:
    def __init__(self, db: Session):
        self.db = db
        self.ups_repo = UPSRepository(db)
        self.pdu_repo = PDURepository(db)
        self.feed_repo = PowerFeedRepository(db)
        self.rack_repo = RackRepository(db)
        self.room_repo = RoomRepository(db)
        self.device_repo = DeviceRepository(db)

    def _serialize_ups(self, ups) -> dict:
        return {
            "id": str(ups.id),
            "company_id": str(ups.company_id),
            "room_id": str(ups.room_id),
            "name": ups.name,
            "model": ups.model,
            "manufacturer": ups.manufacturer,
            "serial_number": ups.serial_number,
            "status": ups.status,
            "capacity_kva": ups.capacity_kva,
            "battery_capacity_minutes": (
                ups.battery_capacity_minutes
            ),
            "input_voltage": ups.input_voltage,
            "output_voltage": ups.output_voltage,
            "efficiency_percent": ups.efficiency_percent,
            "created_at": ups.created_at.isoformat(),
            "updated_at": ups.updated_at.isoformat(),
        }

    def _serialize_pdu(self, pdu) -> dict:
        return {
            "id": str(pdu.id),
            "company_id": str(pdu.company_id),
            "room_id": str(pdu.room_id),
            "name": pdu.name,
            "model": pdu.model,
            "manufacturer": pdu.manufacturer,
            "serial_number": pdu.serial_number,
            "status": pdu.status,
            "rack_id": str(pdu.rack_id)
            if pdu.rack_id
            else None,
            "total_capacity_amp": pdu.total_capacity_amp,
            "current_usage_amp": pdu.current_usage_amp,
            "phase_type": pdu.phase_type,
            "created_at": pdu.created_at.isoformat(),
            "updated_at": pdu.updated_at.isoformat(),
        }

    def _serialize_feed(self, feed) -> dict:
        return {
            "id": str(feed.id),
            "company_id": str(feed.company_id),
            "source_type": feed.source_type,
            "source_id": str(feed.source_id),
            "destination_type": feed.destination_type,
            "destination_id": str(feed.destination_id),
            "voltage": feed.voltage,
            "amp_rating": feed.amp_rating,
            "status": feed.status,
            "created_at": feed.created_at.isoformat(),
            "updated_at": feed.updated_at.isoformat(),
        }

    # --- UPS Methods ---

    def create_ups(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        capacity_kva: float,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str = "ACTIVE",
        battery_capacity_minutes: int | None = None,
        input_voltage: float | None = None,
        output_voltage: float | None = None,
        efficiency_percent: float | None = None,
    ) -> dict:
        if status not in VALID_POWER_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                )
            )

        room = self.room_repo.get_active_by_company_and_id(
            company_id, room_id
        )
        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        existing = self.ups_repo.get_by_room_and_name(
            room_id, name
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A UPS with this name "
                    "already exists in this room"
                )
            )

        if serial_number:
            existing_sn = (
                self.ups_repo.get_by_serial_number(
                    serial_number
                )
            )
            if existing_sn:
                raise DuplicateException(
                    detail=(
                        "A UPS with this serial "
                        "number already exists"
                    )
                )

        ups = self.ups_repo.create(
            company_id=company_id,
            room_id=room_id,
            name=name,
            capacity_kva=capacity_kva,
            model=model,
            manufacturer=manufacturer,
            serial_number=serial_number,
            status=status,
            battery_capacity_minutes=battery_capacity_minutes,
            input_voltage=input_voltage,
            output_voltage=output_voltage,
            efficiency_percent=efficiency_percent,
        )

        self.db.commit()
        self.db.refresh(ups)

        return self._serialize_ups(ups)

    def get_ups(
        self,
        company_id: uuid.UUID,
        ups_id: uuid.UUID,
    ) -> dict:
        ups = self.ups_repo.get_active_by_company_and_id(
            company_id, ups_id
        )

        if not ups:
            raise NotFoundException(
                detail="UPS not found"
            )

        return self._serialize_ups(ups)

    def list_ups(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_POWER_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                    )
                )

        items, total = self.ups_repo.list_by_room(
            company_id=company_id,
            room_id=room_id,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "ups_systems": [
                self._serialize_ups(u) for u in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_ups(
        self,
        company_id: uuid.UUID,
        ups_id: uuid.UUID,
        name: str | None = None,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str | None = None,
        capacity_kva: float | None = None,
        battery_capacity_minutes: int | None = None,
        input_voltage: float | None = None,
        output_voltage: float | None = None,
        efficiency_percent: float | None = None,
    ) -> dict:
        ups = self.ups_repo.get_active_by_company_and_id(
            company_id, ups_id
        )

        if not ups:
            raise NotFoundException(
                detail="UPS not found"
            )

        if status is not None:
            if status not in VALID_POWER_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                    )
                )

        if name is not None and name != ups.name:
            existing = self.ups_repo.get_by_room_and_name(
                ups.room_id, name
            )
            if existing and existing.id != ups.id:
                raise DuplicateException(
                    detail=(
                        "A UPS with this name "
                        "already exists in this room"
                    )
                )

        if (
            serial_number is not None
            and serial_number != ups.serial_number
        ):
            if serial_number:
                existing_sn = (
                    self.ups_repo.get_by_serial_number(
                        serial_number
                    )
                )
                if existing_sn and existing_sn.id != ups.id:
                    raise DuplicateException(
                        detail=(
                            "A UPS with this serial "
                            "number already exists"
                        )
                    )

        self.ups_repo.update(
            ups,
            name=name,
            model=model,
            manufacturer=manufacturer,
            serial_number=serial_number,
            status=status,
            capacity_kva=capacity_kva,
            battery_capacity_minutes=battery_capacity_minutes,
            input_voltage=input_voltage,
            output_voltage=output_voltage,
            efficiency_percent=efficiency_percent,
        )

        self.db.commit()
        self.db.refresh(ups)

        return self._serialize_ups(ups)

    def delete_ups(
        self,
        company_id: uuid.UUID,
        ups_id: uuid.UUID,
    ) -> dict:
        ups = self.ups_repo.get_active_by_company_and_id(
            company_id, ups_id
        )

        if not ups:
            raise NotFoundException(
                detail="UPS not found"
            )

        self.ups_repo.soft_delete(ups)
        self.db.commit()

        return {
            "message": (
                "UPS deleted successfully"
            )
        }

    # --- PDU Methods ---

    def create_pdu(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        total_capacity_amp: float,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str = "ACTIVE",
        rack_id: str | None = None,
        current_usage_amp: float = 0,
        phase_type: str = "SINGLE",
    ) -> dict:
        if status not in VALID_POWER_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                )
            )

        if phase_type not in VALID_PHASE_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid phase_type: {phase_type}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_PHASE_TYPES))}"
                )
            )

        room = self.room_repo.get_active_by_company_and_id(
            company_id, room_id
        )
        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        existing = self.pdu_repo.get_by_room_and_name(
            room_id, name
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A PDU with this name "
                    "already exists in this room"
                )
            )

        if serial_number:
            existing_sn = (
                self.pdu_repo.get_by_serial_number(
                    serial_number
                )
            )
            if existing_sn:
                raise DuplicateException(
                    detail=(
                        "A PDU with this serial "
                        "number already exists"
                    )
                )

        parsed_rack_id = None
        if rack_id is not None:
            parsed_rack_id = uuid.UUID(rack_id)
            rack = (
                self.rack_repo.get_active_by_company_and_id(
                    company_id, parsed_rack_id
                )
            )
            if not rack:
                raise NotFoundException(
                    detail="Rack not found"
                )

        pdu = self.pdu_repo.create(
            company_id=company_id,
            room_id=room_id,
            name=name,
            total_capacity_amp=total_capacity_amp,
            model=model,
            manufacturer=manufacturer,
            serial_number=serial_number,
            status=status,
            rack_id=parsed_rack_id,
            current_usage_amp=current_usage_amp,
            phase_type=phase_type,
        )

        self.db.commit()
        self.db.refresh(pdu)

        return self._serialize_pdu(pdu)

    def get_pdu(
        self,
        company_id: uuid.UUID,
        pdu_id: uuid.UUID,
    ) -> dict:
        pdu = self.pdu_repo.get_active_by_company_and_id(
            company_id, pdu_id
        )

        if not pdu:
            raise NotFoundException(
                detail="PDU not found"
            )

        return self._serialize_pdu(pdu)

    def list_pdus(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_POWER_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                    )
                )

        items, total = self.pdu_repo.list_by_room(
            company_id=company_id,
            room_id=room_id,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "pdus": [
                self._serialize_pdu(p) for p in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_pdu(
        self,
        company_id: uuid.UUID,
        pdu_id: uuid.UUID,
        name: str | None = None,
        model: str | None = None,
        manufacturer: str | None = None,
        serial_number: str | None = None,
        status: str | None = None,
        rack_id: str | None = None,
        total_capacity_amp: float | None = None,
        current_usage_amp: float | None = None,
        phase_type: str | None = None,
    ) -> dict:
        pdu = self.pdu_repo.get_active_by_company_and_id(
            company_id, pdu_id
        )

        if not pdu:
            raise NotFoundException(
                detail="PDU not found"
            )

        if status is not None:
            if status not in VALID_POWER_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                    )
                )

        if phase_type is not None:
            if phase_type not in VALID_PHASE_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid phase_type: {phase_type}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_PHASE_TYPES))}"
                    )
                )

        if name is not None and name != pdu.name:
            existing = self.pdu_repo.get_by_room_and_name(
                pdu.room_id, name
            )
            if existing and existing.id != pdu.id:
                raise DuplicateException(
                    detail=(
                        "A PDU with this name "
                        "already exists in this room"
                    )
                )

        if (
            serial_number is not None
            and serial_number != pdu.serial_number
        ):
            if serial_number:
                existing_sn = (
                    self.pdu_repo.get_by_serial_number(
                        serial_number
                    )
                )
                if existing_sn and existing_sn.id != pdu.id:
                    raise DuplicateException(
                        detail=(
                            "A PDU with this serial "
                            "number already exists"
                        )
                    )

        parsed_rack_id = None
        if rack_id is not None:
            if rack_id:
                parsed_rack_id = uuid.UUID(rack_id)
                rack = (
                    self.rack_repo
                    .get_active_by_company_and_id(
                        company_id, parsed_rack_id
                    )
                )
                if not rack:
                    raise NotFoundException(
                        detail="Rack not found"
                    )
            else:
                parsed_rack_id = None

        self.pdu_repo.update(
            pdu,
            name=name,
            model=model,
            manufacturer=manufacturer,
            serial_number=serial_number,
            status=status,
            rack_id=parsed_rack_id,
            total_capacity_amp=total_capacity_amp,
            current_usage_amp=current_usage_amp,
            phase_type=phase_type,
        )

        self.db.commit()
        self.db.refresh(pdu)

        return self._serialize_pdu(pdu)

    def delete_pdu(
        self,
        company_id: uuid.UUID,
        pdu_id: uuid.UUID,
    ) -> dict:
        pdu = self.pdu_repo.get_active_by_company_and_id(
            company_id, pdu_id
        )

        if not pdu:
            raise NotFoundException(
                detail="PDU not found"
            )

        self.pdu_repo.soft_delete(pdu)
        self.db.commit()

        return {
            "message": (
                "PDU deleted successfully"
            )
        }

    # --- PowerFeed Methods ---

    def create_feed(
        self,
        company_id: uuid.UUID,
        source_type: str,
        source_id: str,
        destination_type: str,
        destination_id: str,
        voltage: float,
        amp_rating: float,
        status: str = "ACTIVE",
    ) -> dict:
        if status not in VALID_POWER_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                )
            )

        if source_type not in VALID_FEED_SOURCE_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid source_type: {source_type}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_FEED_SOURCE_TYPES))}"
                )
            )

        if (
            destination_type
            not in VALID_FEED_DESTINATION_TYPES
        ):
            raise ValidationException(
                detail=(
                    f"Invalid destination_type: "
                    f"{destination_type}. Must be one of: "
                    f"{', '.join(sorted(VALID_FEED_DESTINATION_TYPES))}"
                )
            )

        parsed_source_id = uuid.UUID(source_id)
        parsed_dest_id = uuid.UUID(destination_id)

        if source_type == "UPS":
            source = (
                self.ups_repo.get_active_by_company_and_id(
                    company_id, parsed_source_id
                )
            )
            if not source:
                raise NotFoundException(
                    detail="Source UPS not found"
                )

        if destination_type == "PDU":
            dest = (
                self.pdu_repo.get_active_by_company_and_id(
                    company_id, parsed_dest_id
                )
            )
            if not dest:
                raise NotFoundException(
                    detail="Destination PDU not found"
                )
        elif destination_type == "RACK":
            dest = (
                self.rack_repo.get_active_by_company_and_id(
                    company_id, parsed_dest_id
                )
            )
            if not dest:
                raise NotFoundException(
                    detail="Destination rack not found"
                )

        existing = self.feed_repo.get_by_connection(
            source_type=source_type,
            source_id=parsed_source_id,
            destination_type=destination_type,
            destination_id=parsed_dest_id,
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A power feed with this connection "
                    "already exists"
                )
            )

        feed = self.feed_repo.create(
            company_id=company_id,
            source_type=source_type,
            source_id=parsed_source_id,
            destination_type=destination_type,
            destination_id=parsed_dest_id,
            voltage=voltage,
            amp_rating=amp_rating,
            status=status,
        )

        self.db.commit()
        self.db.refresh(feed)

        return self._serialize_feed(feed)

    def get_feed(
        self,
        company_id: uuid.UUID,
        feed_id: uuid.UUID,
    ) -> dict:
        feed = self.feed_repo.get_active_by_company_and_id(
            company_id, feed_id
        )

        if not feed:
            raise NotFoundException(
                detail="Power feed not found"
            )

        return self._serialize_feed(feed)

    def list_feeds(
        self,
        company_id: uuid.UUID,
        source_type: str | None = None,
        destination_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_POWER_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                    )
                )

        items, total = self.feed_repo.list_by_company(
            company_id=company_id,
            source_type=source_type,
            destination_type=destination_type,
            status=status,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "power_feeds": [
                self._serialize_feed(f) for f in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_feed(
        self,
        company_id: uuid.UUID,
        feed_id: uuid.UUID,
        voltage: float | None = None,
        amp_rating: float | None = None,
        status: str | None = None,
    ) -> dict:
        feed = self.feed_repo.get_active_by_company_and_id(
            company_id, feed_id
        )

        if not feed:
            raise NotFoundException(
                detail="Power feed not found"
            )

        if status is not None:
            if status not in VALID_POWER_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_POWER_STATUSES))}"
                    )
                )

        self.feed_repo.update(
            feed,
            voltage=voltage,
            amp_rating=amp_rating,
            status=status,
        )

        self.db.commit()
        self.db.refresh(feed)

        return self._serialize_feed(feed)

    def delete_feed(
        self,
        company_id: uuid.UUID,
        feed_id: uuid.UUID,
    ) -> dict:
        feed = self.feed_repo.get_active_by_company_and_id(
            company_id, feed_id
        )

        if not feed:
            raise NotFoundException(
                detail="Power feed not found"
            )

        self.feed_repo.soft_delete(feed)
        self.db.commit()

        return {
            "message": (
                "Power feed deleted successfully"
            )
        }

    # --- Power Summary Methods ---

    def get_rack_power(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
    ) -> dict:
        rack = self.rack_repo.get_active_by_company_and_id(
            company_id, rack_id
        )

        if not rack:
            raise NotFoundException(
                detail="Rack not found"
            )

        devices = self.device_repo.get_all_by_rack(rack.id)
        device_power = sum(
            d.power_consumption_watt or 0
            for d in devices
        )

        pdus = self.pdu_repo.list_by_rack(rack.id)
        pdu_details = [
            {
                "pdu_id": str(p.id),
                "name": p.name,
                "total_capacity_amp": p.total_capacity_amp,
                "current_usage_amp": p.current_usage_amp,
                "phase_type": p.phase_type,
            }
            for p in pdus
        ]

        power_capacity_kw = rack.power_capacity_kw
        allocated_kw = device_power / 1000

        available = None
        usage_pct = None
        if power_capacity_kw is not None:
            available = power_capacity_kw - allocated_kw
            if power_capacity_kw > 0:
                usage_pct = round(
                    (allocated_kw / power_capacity_kw) * 100,
                    2,
                )

        return {
            "rack_id": str(rack.id),
            "rack_name": rack.name,
            "power_capacity_kw": power_capacity_kw,
            "allocated_power_kw": round(allocated_kw, 3),
            "available_power_kw": round(available, 3)
            if available is not None
            else None,
            "power_usage_percentage": usage_pct,
            "device_power_watts": device_power,
            "pdus": pdu_details,
        }

    def get_room_power_summary(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
    ) -> dict:
        room = self.room_repo.get_active_by_company_and_id(
            company_id, room_id
        )

        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        ups_list = self.ups_repo.list_all_by_room(room_id)
        pdu_list = self.pdu_repo.list_all_by_room(room_id)

        total_ups_capacity = sum(
            u.capacity_kva for u in ups_list
        )
        total_pdu_capacity = sum(
            p.total_capacity_amp for p in pdu_list
        )

        from app.models.rack import Rack

        racks = (
            self.db.query(Rack)
            .filter(
                Rack.room_id == room_id,
                Rack.deleted_at.is_(None),
            )
            .all()
        )

        total_rack_power = None
        has_capacity = False
        for r in racks:
            if r.power_capacity_kw is not None:
                if not has_capacity:
                    total_rack_power = 0
                    has_capacity = True
                total_rack_power += r.power_capacity_kw

        total_device_power = 0
        for r in racks:
            devices = self.device_repo.get_all_by_rack(r.id)
            total_device_power += sum(
                d.power_consumption_watt or 0
                for d in devices
            )

        ups_details = [
            {
                "ups_id": str(u.id),
                "name": u.name,
                "capacity_kva": u.capacity_kva,
                "status": u.status,
            }
            for u in ups_list
        ]

        pdu_details = [
            {
                "pdu_id": str(p.id),
                "name": p.name,
                "total_capacity_amp": p.total_capacity_amp,
                "current_usage_amp": p.current_usage_amp,
                "status": p.status,
            }
            for p in pdu_list
        ]

        return {
            "room_id": str(room.id),
            "room_name": room.name,
            "total_ups_capacity_kva": total_ups_capacity,
            "total_pdu_capacity_amp": total_pdu_capacity,
            "total_rack_power_capacity_kw": (
                total_rack_power
            ),
            "total_device_power_watts": total_device_power,
            "ups_count": len(ups_list),
            "pdu_count": len(pdu_list),
            "rack_count": len(racks),
            "ups_details": ups_details,
            "pdu_details": pdu_details,
        }

    def get_datacenter_power_summary(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
    ) -> dict:
        from app.models.datacenter import DataCenter

        dc = (
            self.db.query(DataCenter)
            .filter(
                DataCenter.id == datacenter_id,
                DataCenter.company_id == company_id,
                DataCenter.deleted_at.is_(None),
            )
            .first()
        )

        if not dc:
            raise NotFoundException(
                detail="Data center not found"
            )

        from app.models.building import Building
        from app.models.floor import Floor
        from app.models.room import Room

        buildings = (
            self.db.query(Building)
            .filter(
                Building.datacenter_id == datacenter_id,
                Building.deleted_at.is_(None),
            )
            .all()
        )

        building_ids = [b.id for b in buildings]

        if not building_ids:
            rooms = []
        else:
            floors = (
                self.db.query(Floor)
                .filter(
                    Floor.building_id.in_(building_ids),
                    Floor.deleted_at.is_(None),
                )
                .all()
            )

            floor_ids = [f.id for f in floors]

            if not floor_ids:
                rooms = []
            else:
                rooms = (
                    self.db.query(Room)
                    .filter(
                        Room.floor_id.in_(floor_ids),
                        Room.deleted_at.is_(None),
                    )
                    .all()
                )

        room_ids = [r.id for r in rooms]

        ups_list = []
        pdu_list = []
        rack_list = []

        for rid in room_ids:
            ups_list.extend(
                self.ups_repo.list_all_by_room(rid)
            )
            pdu_list.extend(
                self.pdu_repo.list_all_by_room(rid)
            )

        from app.models.rack import Rack

        if room_ids:
            rack_list = (
                self.db.query(Rack)
                .filter(
                    Rack.room_id.in_(room_ids),
                    Rack.deleted_at.is_(None),
                )
                .all()
            )

        total_ups_capacity = sum(
            u.capacity_kva for u in ups_list
        )
        total_pdu_capacity = sum(
            p.total_capacity_amp for p in pdu_list
        )

        total_rack_power = None
        has_capacity = False
        for r in rack_list:
            if r.power_capacity_kw is not None:
                if not has_capacity:
                    total_rack_power = 0
                    has_capacity = True
                total_rack_power += r.power_capacity_kw

        total_device_power = 0
        for r in rack_list:
            devices = self.device_repo.get_all_by_rack(r.id)
            total_device_power += sum(
                d.power_consumption_watt or 0
                for d in devices
            )

        room_summaries = []
        for room in rooms:
            r_ups = [
                u for u in ups_list if u.room_id == room.id
            ]
            r_pdus = [
                p for p in pdu_list if p.room_id == room.id
            ]
            r_racks = [
                r for r in rack_list if r.room_id == room.id
            ]

            r_device_power = 0
            for r in r_racks:
                devs = self.device_repo.get_all_by_rack(
                    r.id
                )
                r_device_power += sum(
                    d.power_consumption_watt or 0
                    for d in devs
                )

            room_summaries.append({
                "room_id": str(room.id),
                "room_name": room.name,
                "ups_count": len(r_ups),
                "pdu_count": len(r_pdus),
                "rack_count": len(r_racks),
                "total_ups_capacity_kva": sum(
                    u.capacity_kva for u in r_ups
                ),
                "total_pdu_capacity_amp": sum(
                    p.total_capacity_amp for p in r_pdus
                ),
                "total_device_power_watts": r_device_power,
            })

        return {
            "datacenter_id": str(dc.id),
            "datacenter_name": dc.name,
            "total_ups_capacity_kva": total_ups_capacity,
            "total_pdu_capacity_amp": total_pdu_capacity,
            "total_rack_power_capacity_kw": (
                total_rack_power
            ),
            "total_device_power_watts": total_device_power,
            "room_count": len(rooms),
            "ups_count": len(ups_list),
            "pdu_count": len(pdu_list),
            "rack_count": len(rack_list),
            "room_summaries": room_summaries,
        }
