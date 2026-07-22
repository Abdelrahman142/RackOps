import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.device import Device


class DeviceRepository:
    def __init__(self, db: Session):
        self.db = db

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
    ) -> Device:
        device = Device(
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
        self.db.add(device)
        self.db.flush()
        return device

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> Device | None:
        return (
            self.db.query(Device)
            .filter(
                Device.id == device_id,
                Device.company_id == company_id,
                Device.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_company_and_name(
        self,
        company_id: uuid.UUID,
        name: str,
    ) -> Device | None:
        return (
            self.db.query(Device)
            .filter(
                Device.company_id == company_id,
                Device.name == name,
                Device.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_serial_number(
        self,
        serial_number: str,
    ) -> Device | None:
        return (
            self.db.query(Device)
            .filter(
                Device.serial_number == serial_number,
                Device.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_asset_tag(
        self,
        asset_tag: str,
    ) -> Device | None:
        return (
            self.db.query(Device)
            .filter(
                Device.asset_tag == asset_tag,
                Device.deleted_at.is_(None),
            )
            .first()
        )

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
    ) -> tuple[list[Device], int]:
        query = self.db.query(Device).filter(
            Device.company_id == company_id,
            Device.rack_id == rack_id,
            Device.deleted_at.is_(None),
        )

        if device_type is not None:
            query = query.filter(
                Device.device_type == device_type
            )

        if status is not None:
            query = query.filter(Device.status == status)

        if vendor is not None:
            query = query.filter(Device.vendor == vendor)

        if search is not None:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Device.name.ilike(search_pattern))
                | (
                    Device.hostname.ilike(
                        search_pattern
                    )
                )
                | (
                    Device.serial_number.ilike(
                        search_pattern
                    )
                )
                | (
                    Device.asset_tag.ilike(
                        search_pattern
                    )
                )
            )

        total = query.count()

        sort_column = getattr(
            Device, sort_by, Device.created_at
        )
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

        return items, total

    def get_all_by_rack(
        self,
        rack_id: uuid.UUID,
    ) -> list[Device]:
        return (
            self.db.query(Device)
            .filter(
                Device.rack_id == rack_id,
                Device.deleted_at.is_(None),
            )
            .all()
        )

    def update(
        self,
        device: Device,
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
    ) -> Device:
        if name is not None:
            device.name = name
        if hostname is not None:
            device.hostname = hostname
        if device_type is not None:
            device.device_type = device_type
        if status is not None:
            device.status = status
        if vendor is not None:
            device.vendor = vendor
        if model is not None:
            device.model = model
        if serial_number is not None:
            device.serial_number = serial_number
        if asset_tag is not None:
            device.asset_tag = asset_tag
        if description is not None:
            device.description = description
        if rack_unit_start is not None:
            device.rack_unit_start = rack_unit_start
        if rack_unit_height is not None:
            device.rack_unit_height = rack_unit_height
        if front_or_rear is not None:
            device.front_or_rear = front_or_rear
        if ip_address is not None:
            device.ip_address = ip_address
        if mac_address is not None:
            device.mac_address = mac_address
        if management_ip is not None:
            device.management_ip = management_ip
        if operating_system is not None:
            device.operating_system = operating_system
        if cpu is not None:
            device.cpu = cpu
        if memory_gb is not None:
            device.memory_gb = memory_gb
        if storage_gb is not None:
            device.storage_gb = storage_gb
        if power_consumption_watt is not None:
            device.power_consumption_watt = (
                power_consumption_watt
            )
        if purchase_date is not None:
            device.purchase_date = purchase_date
        if warranty_end_date is not None:
            device.warranty_end_date = warranty_end_date
        self.db.flush()
        return device

    def soft_delete(self, device: Device) -> Device:
        device.deleted_at = datetime.utcnow()
        self.db.flush()
        return device
