import math
import uuid

from sqlalchemy.orm import Session

from app.repositories.device import DeviceRepository
from app.repositories.rack import RackRepository
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_STATUSES = {
    "ACTIVE",
    "INACTIVE",
    "MAINTENANCE",
    "FAILED",
    "DECOMMISSIONED",
}

VALID_DEVICE_TYPES = {
    "SERVER",
    "SWITCH",
    "ROUTER",
    "FIREWALL",
    "STORAGE",
    "UPS",
    "PDU",
    "LOAD_BALANCER",
    "PATCH_PANEL",
    "OTHER",
}

VALID_FRONT_OR_REAR = {"FRONT", "REAR"}

SORTABLE_FIELDS = {
    "name",
    "hostname",
    "device_type",
    "status",
    "vendor",
    "serial_number",
    "asset_tag",
    "rack_unit_start",
    "rack_unit_height",
    "power_consumption_watt",
    "created_at",
    "updated_at",
}


class DeviceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DeviceRepository(db)
        self.rack_repo = RackRepository(db)

    def _check_rack_overlap(
        self,
        rack_id: uuid.UUID,
        rack_unit_start: int,
        rack_unit_height: int,
        exclude_device_id: uuid.UUID | None = None,
    ) -> list[dict]:
        devices = self.repo.get_all_by_rack(rack_id)
        overlapping = []

        new_start = rack_unit_start
        new_end = rack_unit_start + rack_unit_height - 1

        for d in devices:
            if exclude_device_id and d.id == exclude_device_id:
                continue
            if d.rack_unit_start is None:
                continue
            d_start = d.rack_unit_start
            d_end = d_start + d.rack_unit_height - 1

            if new_start <= d_end and new_end >= d_start:
                overlapping.append({
                    "device_id": str(d.id),
                    "device_name": d.name,
                    "device_type": d.device_type,
                    "rack_unit_start": d.rack_unit_start,
                    "rack_unit_height": d.rack_unit_height,
                })

        return overlapping

    def _validate_placement(
        self,
        rack,
        rack_unit_start: int,
        rack_unit_height: int,
        exclude_device_id: uuid.UUID | None = None,
    ) -> None:
        if rack_unit_start + rack_unit_height - 1 > rack.height_units:
            raise ValidationException(
                detail=(
                    f"Device placement exceeds rack "
                    f"capacity. Rack has "
                    f"{rack.height_units}U but device "
                    f"would occupy U{rack_unit_start}-"
                    f"U{rack_unit_start + rack_unit_height - 1}"
                )
            )

        overlapping = self._check_rack_overlap(
            rack.id, rack_unit_start, rack_unit_height,
            exclude_device_id,
        )
        if overlapping:
            overlap_desc = ", ".join(
                [
                    f"{o['device_name']} "
                    f"(U{o['rack_unit_start']}-"
                    f"U{o['rack_unit_start'] + o['rack_unit_height'] - 1})"
                    for o in overlapping
                ]
            )
            raise ValidationException(
                detail=(
                    f"Rack unit overlap detected with "
                    f"existing device(s): {overlap_desc}"
                )
            )

    def _validate_power(
        self,
        rack,
        power_consumption_watt: int | None,
        exclude_device_id: uuid.UUID | None = None,
    ) -> None:
        if power_consumption_watt is None:
            return
        if rack.power_capacity_kw is None:
            return

        devices = self.repo.get_all_by_rack(rack.id)
        existing_power = sum(
            d.power_consumption_watt or 0
            for d in devices
            if not exclude_device_id
            or d.id != exclude_device_id
        )

        total_power_w = existing_power + power_consumption_watt
        rack_capacity_w = rack.power_capacity_kw * 1000

        if total_power_w > rack_capacity_w:
            raise ValidationException(
                detail=(
                    f"Power consumption would exceed "
                    f"rack capacity. Rack capacity: "
                    f"{rack.power_capacity_kw}kW, "
                    f"existing usage: "
                    f"{existing_power}W, "
                    f"new device: "
                    f"{power_consumption_watt}W"
                )
            )

    def _serialize(self, device) -> dict:
        return {
            "id": str(device.id),
            "company_id": str(device.company_id),
            "rack_id": str(device.rack_id),
            "name": device.name,
            "hostname": device.hostname,
            "device_type": device.device_type,
            "status": device.status,
            "vendor": device.vendor,
            "model": device.model,
            "serial_number": device.serial_number,
            "asset_tag": device.asset_tag,
            "description": device.description,
            "rack_unit_start": device.rack_unit_start,
            "rack_unit_height": device.rack_unit_height,
            "front_or_rear": device.front_or_rear,
            "ip_address": device.ip_address,
            "mac_address": device.mac_address,
            "management_ip": device.management_ip,
            "operating_system": device.operating_system,
            "cpu": device.cpu,
            "memory_gb": device.memory_gb,
            "storage_gb": device.storage_gb,
            "power_consumption_watt": (
                device.power_consumption_watt
            ),
            "purchase_date": device.purchase_date,
            "warranty_end_date": device.warranty_end_date,
            "created_at": device.created_at.isoformat(),
            "updated_at": device.updated_at.isoformat(),
        }

    def create(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
        name: str,
        hostname: str | None = None,
        device_type: str = "SERVER",
        status: str = "ACTIVE",
        vendor: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        asset_tag: str | None = None,
        description: str | None = None,
        rack_unit_start: int | None = None,
        rack_unit_height: int = 1,
        front_or_rear: str | None = None,
        ip_address: str | None = None,
        mac_address: str | None = None,
        management_ip: str | None = None,
        operating_system: str | None = None,
        cpu: str | None = None,
        memory_gb: int | None = None,
        storage_gb: int | None = None,
        power_consumption_watt: int | None = None,
        purchase_date: str | None = None,
        warranty_end_date: str | None = None,
    ) -> dict:
        if status not in VALID_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_STATUSES))}"
                )
            )

        if device_type not in VALID_DEVICE_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid device_type: {device_type}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_DEVICE_TYPES))}"
                )
            )

        if (
            front_or_rear is not None
            and front_or_rear not in VALID_FRONT_OR_REAR
        ):
            raise ValidationException(
                detail=(
                    f"Invalid front_or_rear: "
                    f"{front_or_rear}. "
                    "Must be FRONT or REAR"
                )
            )

        rack = self.rack_repo.get_active_by_company_and_id(
            company_id, rack_id
        )
        if not rack:
            raise NotFoundException(
                detail="Rack not found"
            )

        existing = self.repo.get_by_company_and_name(
            company_id, name
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A device with this name "
                    "already exists in your company"
                )
            )

        if serial_number:
            existing_sn = self.repo.get_by_serial_number(
                serial_number
            )
            if existing_sn:
                raise DuplicateException(
                    detail=(
                        "A device with this serial "
                        "number already exists"
                    )
                )

        if asset_tag:
            existing_tag = self.repo.get_by_asset_tag(
                asset_tag
            )
            if existing_tag:
                raise DuplicateException(
                    detail=(
                        "A device with this asset "
                        "tag already exists"
                    )
                )

        if rack_unit_start is not None:
            self._validate_placement(
                rack, rack_unit_start, rack_unit_height
            )

        self._validate_power(
            rack, power_consumption_watt
        )

        device = self.repo.create(
            company_id=company_id,
            rack_id=rack_id,
            name=name,
            hostname=hostname,
            device_type=device_type,
            status=status,
            vendor=vendor,
            model=model,
            serial_number=serial_number,
            asset_tag=asset_tag,
            description=description,
            rack_unit_start=rack_unit_start,
            rack_unit_height=rack_unit_height,
            front_or_rear=front_or_rear,
            ip_address=ip_address,
            mac_address=mac_address,
            management_ip=management_ip,
            operating_system=operating_system,
            cpu=cpu,
            memory_gb=memory_gb,
            storage_gb=storage_gb,
            power_consumption_watt=power_consumption_watt,
            purchase_date=purchase_date,
            warranty_end_date=warranty_end_date,
        )

        self.db.commit()
        self.db.refresh(device)

        return self._serialize(device)

    def get(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> dict:
        device = self.repo.get_active_by_company_and_id(
            company_id, device_id
        )

        if not device:
            raise NotFoundException(
                detail="Device not found"
            )

        return self._serialize(device)

    def list_by_rack(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
        device_type: str | None = None,
        status: str | None = None,
        vendor: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_STATUSES))}"
                    )
                )

        if device_type is not None:
            if device_type not in VALID_DEVICE_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid device_type filter: "
                        f"{device_type}. Must be one of: "
                        f"{', '.join(sorted(VALID_DEVICE_TYPES))}"
                    )
                )

        if sort_by not in SORTABLE_FIELDS:
            raise ValidationException(
                detail=(
                    f"Invalid sort field: {sort_by}. "
                    "Must be one of: "
                    f"{', '.join(sorted(SORTABLE_FIELDS))}"
                )
            )

        if sort_order not in ("asc", "desc"):
            raise ValidationException(
                detail=(
                    "Invalid sort order. "
                    "Must be 'asc' or 'desc'"
                )
            )

        if page < 1:
            page = 1
        if size < 1:
            size = 1
        if size > 100:
            size = 100

        items, total = self.repo.list_by_rack(
            company_id=company_id,
            rack_id=rack_id,
            device_type=device_type,
            status=status,
            vendor=vendor,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "devices": [
                self._serialize(d) for d in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        name: str | None = None,
        hostname: str | None = None,
        device_type: str | None = None,
        status: str | None = None,
        vendor: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        asset_tag: str | None = None,
        description: str | None = None,
        rack_unit_start: int | None = None,
        rack_unit_height: int | None = None,
        front_or_rear: str | None = None,
        ip_address: str | None = None,
        mac_address: str | None = None,
        management_ip: str | None = None,
        operating_system: str | None = None,
        cpu: str | None = None,
        memory_gb: int | None = None,
        storage_gb: int | None = None,
        power_consumption_watt: int | None = None,
        purchase_date: str | None = None,
        warranty_end_date: str | None = None,
    ) -> dict:
        device = self.repo.get_active_by_company_and_id(
            company_id, device_id
        )

        if not device:
            raise NotFoundException(
                detail="Device not found"
            )

        if status is not None:
            if status not in VALID_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_STATUSES))}"
                    )
                )

        if device_type is not None:
            if device_type not in VALID_DEVICE_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid device_type: "
                        f"{device_type}. Must be one of: "
                        f"{', '.join(sorted(VALID_DEVICE_TYPES))}"
                    )
                )

        if (
            front_or_rear is not None
            and front_or_rear not in VALID_FRONT_OR_REAR
        ):
            raise ValidationException(
                detail=(
                    f"Invalid front_or_rear: "
                    f"{front_or_rear}. "
                    "Must be FRONT or REAR"
                )
            )

        if name is not None and name != device.name:
            existing = self.repo.get_by_company_and_name(
                company_id, name
            )
            if existing and existing.id != device.id:
                raise DuplicateException(
                    detail=(
                        "A device with this name "
                        "already exists in your company"
                    )
                )

        if (
            serial_number is not None
            and serial_number != device.serial_number
        ):
            if serial_number:
                existing_sn = (
                    self.repo.get_by_serial_number(
                        serial_number
                    )
                )
                if existing_sn and existing_sn.id != device.id:
                    raise DuplicateException(
                        detail=(
                            "A device with this serial "
                            "number already exists"
                        )
                    )

        if (
            asset_tag is not None
            and asset_tag != device.asset_tag
        ):
            if asset_tag:
                existing_tag = (
                    self.repo.get_by_asset_tag(asset_tag)
                )
                if existing_tag and existing_tag.id != device.id:
                    raise DuplicateException(
                        detail=(
                            "A device with this asset "
                            "tag already exists"
                        )
                    )

        rack = self.rack_repo.get_active_by_company_and_id(
            company_id, device.rack_id
        )

        final_start = (
            rack_unit_start
            if rack_unit_start is not None
            else device.rack_unit_start
        )
        final_height = (
            rack_unit_height
            if rack_unit_height is not None
            else device.rack_unit_height
        )

        if final_start is not None:
            self._validate_placement(
                rack,
                final_start,
                final_height,
                exclude_device_id=device.id,
            )

        final_power = (
            power_consumption_watt
            if power_consumption_watt is not None
            else device.power_consumption_watt
        )
        self._validate_power(
            rack, final_power, exclude_device_id=device.id
        )

        self.repo.update(
            device,
            name=name,
            hostname=hostname,
            device_type=device_type,
            status=status,
            vendor=vendor,
            model=model,
            serial_number=serial_number,
            asset_tag=asset_tag,
            description=description,
            rack_unit_start=rack_unit_start,
            rack_unit_height=rack_unit_height,
            front_or_rear=front_or_rear,
            ip_address=ip_address,
            mac_address=mac_address,
            management_ip=management_ip,
            operating_system=operating_system,
            cpu=cpu,
            memory_gb=memory_gb,
            storage_gb=storage_gb,
            power_consumption_watt=power_consumption_watt,
            purchase_date=purchase_date,
            warranty_end_date=warranty_end_date,
        )

        self.db.commit()
        self.db.refresh(device)

        return self._serialize(device)

    def delete(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> dict:
        device = self.repo.get_active_by_company_and_id(
            company_id, device_id
        )

        if not device:
            raise NotFoundException(
                detail="Device not found"
            )

        self.repo.soft_delete(device)
        self.db.commit()

        return {
            "message": (
                "Device deleted successfully"
            )
        }

    def get_rack_layout(
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

        devices = self.repo.get_all_by_rack(rack.id)
        total_u = rack.height_units
        positions = []
        used_units = 0

        occupied_map = {}
        for d in devices:
            if d.rack_unit_start is not None:
                for u in range(
                    d.rack_unit_start,
                    d.rack_unit_start + d.rack_unit_height,
                ):
                    occupied_map[u] = d

        for u in range(1, total_u + 1):
            if u in occupied_map:
                d = occupied_map[u]
                positions.append({
                    "unit": u,
                    "occupied": True,
                    "device_id": str(d.id),
                    "device_name": d.name,
                    "device_type": d.device_type,
                })
                if d.rack_unit_start == u:
                    used_units += d.rack_unit_height
            else:
                positions.append({
                    "unit": u,
                    "occupied": False,
                    "device_id": None,
                    "device_name": None,
                    "device_type": None,
                })

        return {
            "rack_id": str(rack.id),
            "rack_name": rack.name,
            "total_units": total_u,
            "used_units": used_units,
            "available_units": total_u - used_units,
            "positions": positions,
        }

    def check_placement(
        self,
        company_id: uuid.UUID,
        rack_id: uuid.UUID,
        rack_unit_start: int,
        rack_unit_height: int,
        device_id: str | None = None,
    ) -> dict:
        rack = self.rack_repo.get_active_by_company_and_id(
            company_id, rack_id
        )

        if not rack:
            raise NotFoundException(
                detail="Rack not found"
            )

        exclude_id = None
        if device_id:
            try:
                exclude_id = uuid.UUID(device_id)
            except ValueError:
                raise ValidationException(
                    detail="Invalid device_id format"
                )

        if rack_unit_start < 1:
            raise ValidationException(
                detail="rack_unit_start must be >= 1"
            )

        if rack_unit_start + rack_unit_height - 1 > rack.height_units:
            return {
                "fits": False,
                "reason": (
                    f"Device would exceed rack "
                    f"capacity ({rack.height_units}U)"
                ),
                "rack_unit_start": rack_unit_start,
                "rack_unit_height": rack_unit_height,
                "overlapping_devices": [],
            }

        overlapping = self._check_rack_overlap(
            rack.id,
            rack_unit_start,
            rack_unit_height,
            exclude_id,
        )

        if overlapping:
            return {
                "fits": False,
                "reason": (
                    "Rack units overlap with "
                    "existing device(s)"
                ),
                "rack_unit_start": rack_unit_start,
                "rack_unit_height": rack_unit_height,
                "overlapping_devices": overlapping,
            }

        return {
            "fits": True,
            "reason": "Placement is available",
            "rack_unit_start": rack_unit_start,
            "rack_unit_height": rack_unit_height,
            "overlapping_devices": [],
        }
