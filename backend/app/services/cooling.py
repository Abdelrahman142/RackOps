import math
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.cooling_unit import (
    CoolingUnitRepository,
)
from app.repositories.environmental_zone import (
    EnvironmentalZoneRepository,
)
from app.repositories.room import RoomRepository
from app.repositories.sensor import SensorRepository
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_COOLING_STATUSES = {
    "ACTIVE",
    "WARNING",
    "FAILED",
    "MAINTENANCE",
    "OFFLINE",
}

VALID_COOLING_TYPES = {
    "CRAC",
    "CRAH",
    "CHILLER",
    "FAN_WALL",
    "OTHER",
}

VALID_SENSOR_TYPES = {
    "TEMPERATURE",
    "HUMIDITY",
    "POWER",
    "AIRFLOW",
    "SMOKE",
    "WATER_LEAK",
    "OTHER",
}


class CoolingService:
    def __init__(self, db: Session):
        self.db = db
        self.cooling_repo = CoolingUnitRepository(db)
        self.zone_repo = EnvironmentalZoneRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.room_repo = RoomRepository(db)

    def _serialize_unit(self, unit) -> dict:
        return {
            "id": str(unit.id),
            "company_id": str(unit.company_id),
            "room_id": str(unit.room_id),
            "name": unit.name,
            "manufacturer": unit.manufacturer,
            "model": unit.model,
            "serial_number": unit.serial_number,
            "type": unit.type,
            "status": unit.status,
            "cooling_capacity_kw": unit.cooling_capacity_kw,
            "airflow_cfm": unit.airflow_cfm,
            "power_consumption_kw": (
                unit.power_consumption_kw
            ),
            "created_at": unit.created_at.isoformat(),
            "updated_at": unit.updated_at.isoformat(),
        }

    def _serialize_zone(self, zone) -> dict:
        return {
            "id": str(zone.id),
            "company_id": str(zone.company_id),
            "room_id": str(zone.room_id),
            "name": zone.name,
            "description": zone.description,
            "target_temperature_min": (
                zone.target_temperature_min
            ),
            "target_temperature_max": (
                zone.target_temperature_max
            ),
            "target_humidity_min": (
                zone.target_humidity_min
            ),
            "target_humidity_max": (
                zone.target_humidity_max
            ),
            "status": zone.status,
            "created_at": zone.created_at.isoformat(),
            "updated_at": zone.updated_at.isoformat(),
        }

    def _serialize_sensor(self, sensor) -> dict:
        return {
            "id": str(sensor.id),
            "company_id": str(sensor.company_id),
            "zone_id": str(sensor.zone_id),
            "name": sensor.name,
            "sensor_type": sensor.sensor_type,
            "status": sensor.status,
            "location_description": (
                sensor.location_description
            ),
            "last_value": sensor.last_value,
            "last_unit": sensor.last_unit,
            "last_reading_at": (
                sensor.last_reading_at.isoformat()
                if sensor.last_reading_at
                else None
            ),
            "created_at": sensor.created_at.isoformat(),
            "updated_at": sensor.updated_at.isoformat(),
        }

    # --- Cooling Unit Methods ---

    def create_unit(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        cooling_capacity_kw: float,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        type: str = "CRAC",
        status: str = "ACTIVE",
        airflow_cfm: float | None = None,
        power_consumption_kw: float | None = None,
    ) -> dict:
        if status not in VALID_COOLING_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                )
            )

        if type not in VALID_COOLING_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid type: {type}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_COOLING_TYPES))}"
                )
            )

        room = self.room_repo.get_active_by_company_and_id(
            company_id, room_id
        )
        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        existing = self.cooling_repo.get_by_room_and_name(
            room_id, name
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A cooling unit with this name "
                    "already exists in this room"
                )
            )

        if serial_number:
            existing_sn = (
                self.cooling_repo.get_by_serial_number(
                    serial_number
                )
            )
            if existing_sn:
                raise DuplicateException(
                    detail=(
                        "A cooling unit with this serial "
                        "number already exists"
                    )
                )

        unit = self.cooling_repo.create(
            company_id=company_id,
            room_id=room_id,
            name=name,
            cooling_capacity_kw=cooling_capacity_kw,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            type=type,
            status=status,
            airflow_cfm=airflow_cfm,
            power_consumption_kw=power_consumption_kw,
        )

        self.db.commit()
        self.db.refresh(unit)

        return self._serialize_unit(unit)

    def get_unit(
        self,
        company_id: uuid.UUID,
        unit_id: uuid.UUID,
    ) -> dict:
        unit = self.cooling_repo.get_active_by_company_and_id(
            company_id, unit_id
        )

        if not unit:
            raise NotFoundException(
                detail="Cooling unit not found"
            )

        return self._serialize_unit(unit)

    def list_units(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        status: str | None = None,
        type: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_COOLING_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                    )
                )

        if type is not None:
            if type not in VALID_COOLING_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid type filter: "
                        f"{type}. Must be one of: "
                        f"{', '.join(sorted(VALID_COOLING_TYPES))}"
                    )
                )

        items, total = self.cooling_repo.list_by_room(
            company_id=company_id,
            room_id=room_id,
            status=status,
            type=type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "cooling_units": [
                self._serialize_unit(u) for u in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_unit(
        self,
        company_id: uuid.UUID,
        unit_id: uuid.UUID,
        name: str | None = None,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        type: str | None = None,
        status: str | None = None,
        cooling_capacity_kw: float | None = None,
        airflow_cfm: float | None = None,
        power_consumption_kw: float | None = None,
    ) -> dict:
        unit = self.cooling_repo.get_active_by_company_and_id(
            company_id, unit_id
        )

        if not unit:
            raise NotFoundException(
                detail="Cooling unit not found"
            )

        if status is not None:
            if status not in VALID_COOLING_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                    )
                )

        if type is not None:
            if type not in VALID_COOLING_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid type: {type}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_COOLING_TYPES))}"
                    )
                )

        if name is not None and name != unit.name:
            existing = (
                self.cooling_repo.get_by_room_and_name(
                    unit.room_id, name
                )
            )
            if existing and existing.id != unit.id:
                raise DuplicateException(
                    detail=(
                        "A cooling unit with this name "
                        "already exists in this room"
                    )
                )

        if (
            serial_number is not None
            and serial_number != unit.serial_number
        ):
            if serial_number:
                existing_sn = (
                    self.cooling_repo.get_by_serial_number(
                        serial_number
                    )
                )
                if existing_sn and existing_sn.id != unit.id:
                    raise DuplicateException(
                        detail=(
                            "A cooling unit with this "
                            "serial number already exists"
                        )
                    )

        self.cooling_repo.update(
            unit,
            name=name,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            type=type,
            status=status,
            cooling_capacity_kw=cooling_capacity_kw,
            airflow_cfm=airflow_cfm,
            power_consumption_kw=power_consumption_kw,
        )

        self.db.commit()
        self.db.refresh(unit)

        return self._serialize_unit(unit)

    def delete_unit(
        self,
        company_id: uuid.UUID,
        unit_id: uuid.UUID,
    ) -> dict:
        unit = self.cooling_repo.get_active_by_company_and_id(
            company_id, unit_id
        )

        if not unit:
            raise NotFoundException(
                detail="Cooling unit not found"
            )

        self.cooling_repo.soft_delete(unit)
        self.db.commit()

        return {
            "message": (
                "Cooling unit deleted successfully"
            )
        }

    # --- Zone Methods ---

    def create_zone(
        self,
        company_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str,
        description: str | None = None,
        target_temperature_min: float | None = None,
        target_temperature_max: float | None = None,
        target_humidity_min: float | None = None,
        target_humidity_max: float | None = None,
        status: str = "ACTIVE",
    ) -> dict:
        if status not in VALID_COOLING_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                )
            )

        if (
            target_temperature_min is not None
            and target_temperature_max is not None
            and target_temperature_min
            > target_temperature_max
        ):
            raise ValidationException(
                detail=(
                    "target_temperature_min must be "
                    "<= target_temperature_max"
                )
            )

        if (
            target_humidity_min is not None
            and target_humidity_max is not None
            and target_humidity_min > target_humidity_max
        ):
            raise ValidationException(
                detail=(
                    "target_humidity_min must be "
                    "<= target_humidity_max"
                )
            )

        room = self.room_repo.get_active_by_company_and_id(
            company_id, room_id
        )
        if not room:
            raise NotFoundException(
                detail="Room not found"
            )

        existing = self.zone_repo.get_by_room_and_name(
            room_id, name
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A zone with this name "
                    "already exists in this room"
                )
            )

        zone = self.zone_repo.create(
            company_id=company_id,
            room_id=room_id,
            name=name,
            description=description,
            target_temperature_min=target_temperature_min,
            target_temperature_max=target_temperature_max,
            target_humidity_min=target_humidity_min,
            target_humidity_max=target_humidity_max,
            status=status,
        )

        self.db.commit()
        self.db.refresh(zone)

        return self._serialize_zone(zone)

    def get_zone(
        self,
        company_id: uuid.UUID,
        zone_id: uuid.UUID,
    ) -> dict:
        zone = self.zone_repo.get_active_by_company_and_id(
            company_id, zone_id
        )

        if not zone:
            raise NotFoundException(
                detail="Zone not found"
            )

        return self._serialize_zone(zone)

    def list_zones(
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
            if status not in VALID_COOLING_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                    )
                )

        items, total = self.zone_repo.list_by_room(
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
            "zones": [
                self._serialize_zone(z) for z in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_zone(
        self,
        company_id: uuid.UUID,
        zone_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        target_temperature_min: float | None = None,
        target_temperature_max: float | None = None,
        target_humidity_min: float | None = None,
        target_humidity_max: float | None = None,
        status: str | None = None,
    ) -> dict:
        zone = self.zone_repo.get_active_by_company_and_id(
            company_id, zone_id
        )

        if not zone:
            raise NotFoundException(
                detail="Zone not found"
            )

        if status is not None:
            if status not in VALID_COOLING_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                    )
                )

        if name is not None and name != zone.name:
            existing = self.zone_repo.get_by_room_and_name(
                zone.room_id, name
            )
            if existing and existing.id != zone.id:
                raise DuplicateException(
                    detail=(
                        "A zone with this name "
                        "already exists in this room"
                    )
                )

        self.zone_repo.update(
            zone,
            name=name,
            description=description,
            target_temperature_min=target_temperature_min,
            target_temperature_max=target_temperature_max,
            target_humidity_min=target_humidity_min,
            target_humidity_max=target_humidity_max,
            status=status,
        )

        self.db.commit()
        self.db.refresh(zone)

        return self._serialize_zone(zone)

    # --- Sensor Methods ---

    def create_sensor(
        self,
        company_id: uuid.UUID,
        zone_id: uuid.UUID,
        name: str,
        sensor_type: str,
        status: str = "ACTIVE",
        location_description: str | None = None,
    ) -> dict:
        if status not in VALID_COOLING_STATUSES:
            raise ValidationException(
                detail=(
                    f"Invalid status: {status}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                )
            )

        if sensor_type not in VALID_SENSOR_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid sensor_type: {sensor_type}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_SENSOR_TYPES))}"
                )
            )

        zone = self.zone_repo.get_active_by_company_and_id(
            company_id, zone_id
        )
        if not zone:
            raise NotFoundException(
                detail="Zone not found"
            )

        existing = self.sensor_repo.get_by_zone_and_name(
            zone_id, name
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A sensor with this name "
                    "already exists in this zone"
                )
            )

        sensor = self.sensor_repo.create(
            company_id=company_id,
            zone_id=zone_id,
            name=name,
            sensor_type=sensor_type,
            status=status,
            location_description=location_description,
        )

        self.db.commit()
        self.db.refresh(sensor)

        return self._serialize_sensor(sensor)

    def get_sensor(
        self,
        company_id: uuid.UUID,
        sensor_id: uuid.UUID,
    ) -> dict:
        sensor = self.sensor_repo.get_active_by_company_and_id(
            company_id, sensor_id
        )

        if not sensor:
            raise NotFoundException(
                detail="Sensor not found"
            )

        return self._serialize_sensor(sensor)

    def list_sensors(
        self,
        company_id: uuid.UUID,
        zone_id: uuid.UUID,
        status: str | None = None,
        sensor_type: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if status is not None:
            if status not in VALID_COOLING_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}. "
                        "Must be one of: "
                        f"{', '.join(sorted(VALID_COOLING_STATUSES))}"
                    )
                )

        if sensor_type is not None:
            if sensor_type not in VALID_SENSOR_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid sensor_type filter: "
                        f"{sensor_type}. Must be one of: "
                        f"{', '.join(sorted(VALID_SENSOR_TYPES))}"
                    )
                )

        items, total = self.sensor_repo.list_by_zone(
            company_id=company_id,
            zone_id=zone_id,
            status=status,
            sensor_type=sensor_type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "sensors": [
                self._serialize_sensor(s) for s in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    # --- Environmental Monitoring Engine ---

    def _evaluate_temperature(
        self,
        value: float,
        t_min: float | None,
        t_max: float | None,
    ) -> str:
        if t_min is None or t_max is None:
            return "NORMAL"

        if value < t_min or value > t_max:
            margin_below = (
                t_min - value if value < t_min else 0
            )
            margin_above = (
                value - t_max if value > t_max else 0
            )
            margin = max(margin_below, margin_above)
            if margin > 5:
                return "CRITICAL"
            return "WARNING"

        return "NORMAL"

    def _evaluate_humidity(
        self,
        value: float,
        h_min: float | None,
        h_max: float | None,
    ) -> str:
        if h_min is None or h_max is None:
            return "NORMAL"

        if value < h_min or value > h_max:
            margin_below = (
                h_min - value if value < h_min else 0
            )
            margin_above = (
                value - h_max if value > h_max else 0
            )
            margin = max(margin_below, margin_above)
            if margin > 10:
                return "CRITICAL"
            return "WARNING"

        return "NORMAL"

    def _get_room_temperature_humidity(
        self,
        room_id: uuid.UUID,
    ) -> tuple[float | None, float | None, str | None, str | None]:
        from app.models.room import Room

        room = (
            self.db.query(Room)
            .filter(Room.id == room_id)
            .first()
        )

        temp_unit = None
        hum_unit = None

        zones = self.zone_repo.list_all_by_room(room_id)
        zone_ids = [z.id for z in zones]

        temp_sensors = self.sensor_repo.list_by_type_in_zones(
            zone_ids, "TEMPERATURE"
        )
        hum_sensors = self.sensor_repo.list_by_type_in_zones(
            zone_ids, "HUMIDITY"
        )

        temp_values = [
            s.last_value
            for s in temp_sensors
            if s.last_value is not None
        ]
        hum_values = [
            s.last_value
            for s in hum_sensors
            if s.last_value is not None
        ]

        avg_temp = (
            round(sum(temp_values) / len(temp_values), 1)
            if temp_values
            else None
        )
        avg_hum = (
            round(sum(hum_values) / len(hum_values), 1)
            if hum_values
            else None
        )

        if temp_sensors:
            for s in temp_sensors:
                if s.last_unit:
                    temp_unit = s.last_unit
                    break

        if hum_sensors:
            for s in hum_sensors:
                if s.last_unit:
                    hum_unit = s.last_unit
                    break

        return avg_temp, avg_hum, temp_unit, hum_unit

    def _get_zone_health(
        self,
        zone,
        avg_temp: float | None,
        avg_hum: float | None,
    ) -> str:
        readings = []

        if avg_temp is not None:
            readings.append(
                self._evaluate_temperature(
                    avg_temp,
                    zone.target_temperature_min,
                    zone.target_temperature_max,
                )
            )

        if avg_hum is not None:
            readings.append(
                self._evaluate_humidity(
                    avg_hum,
                    zone.target_humidity_min,
                    zone.target_humidity_max,
                )
            )

        if "CRITICAL" in readings:
            return "CRITICAL"
        if "WARNING" in readings:
            return "WARNING"
        return "NORMAL"

    def get_room_environment_summary(
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

        units = self.cooling_repo.list_all_by_room(room_id)
        zones = self.zone_repo.list_all_by_room(room_id)

        active_units = [
            u for u in units if u.status == "ACTIVE"
        ]
        failed_units = [
            u for u in units if u.status == "FAILED"
        ]

        total_capacity = sum(
            u.cooling_capacity_kw for u in active_units
        )

        avg_temp, avg_hum, temp_unit, hum_unit = (
            self._get_room_temperature_humidity(room_id)
        )

        cooling_status = "NORMAL"
        if failed_units:
            cooling_status = "WARNING"
            if len(failed_units) >= len(units) and units:
                cooling_status = "CRITICAL"

        warnings = []
        for u in failed_units:
            warnings.append({
                "type": "COOLING_UNIT_FAILED",
                "severity": "CRITICAL",
                "message": (
                    f"Cooling unit '{u.name}' "
                    f"is in FAILED status"
                ),
                "entity_type": "COOLING_UNIT",
                "entity_id": str(u.id),
            })

        zone_details = []
        overall_health = "NORMAL"

        for zone in zones:
            zone_health = self._get_zone_health(
                zone, avg_temp, avg_hum
            )

            if zone_health == "CRITICAL":
                overall_health = "CRITICAL"
            elif (
                zone_health == "WARNING"
                and overall_health != "CRITICAL"
            ):
                overall_health = "WARNING"

            if avg_temp is not None and zone_health != "NORMAL":
                if (
                    zone.target_temperature_min is not None
                    and avg_temp
                    < zone.target_temperature_min
                ):
                    warnings.append({
                        "type": "TEMPERATURE_LOW",
                        "severity": zone_health,
                        "message": (
                            f"Zone '{zone.name}': "
                            f"Temperature {avg_temp}C "
                            f"below minimum "
                            f"{zone.target_temperature_min}C"
                        ),
                        "entity_type": "ZONE",
                        "entity_id": str(zone.id),
                    })
                elif (
                    zone.target_temperature_max is not None
                    and avg_temp
                    > zone.target_temperature_max
                ):
                    warnings.append({
                        "type": "TEMPERATURE_HIGH",
                        "severity": zone_health,
                        "message": (
                            f"Zone '{zone.name}': "
                            f"Temperature {avg_temp}C "
                            f"above maximum "
                            f"{zone.target_temperature_max}C"
                        ),
                        "entity_type": "ZONE",
                        "entity_id": str(zone.id),
                    })

            zone_details.append({
                "zone_id": str(zone.id),
                "zone_name": zone.name,
                "health": zone_health,
                "target_temperature_range": [
                    zone.target_temperature_min,
                    zone.target_temperature_max,
                ],
                "target_humidity_range": [
                    zone.target_humidity_min,
                    zone.target_humidity_max,
                ],
            })

        return {
            "room_id": str(room.id),
            "room_name": room.name,
            "current_temperature": avg_temp,
            "current_humidity": avg_hum,
            "temperature_unit": temp_unit,
            "humidity_unit": hum_unit,
            "cooling_status": cooling_status,
            "cooling_capacity_kw": round(total_capacity, 2),
            "active_cooling_units": len(active_units),
            "total_cooling_units": len(units),
            "active_warnings": warnings,
            "environmental_health": overall_health,
            "zones": zone_details,
        }

    def get_datacenter_environment_summary(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
    ) -> dict:
        from app.models.building import Building
        from app.models.datacenter import DataCenter
        from app.models.floor import Floor
        from app.models.room import Room

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
            all_rooms = []
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
                all_rooms = []
            else:
                all_rooms = (
                    self.db.query(Room)
                    .filter(
                        Room.floor_id.in_(floor_ids),
                        Room.deleted_at.is_(None),
                    )
                    .all()
                )

        all_units = []
        all_temps = []
        all_hums = []
        critical_rooms = []
        failed_units = []
        room_summaries = []

        for room in all_rooms:
            units = self.cooling_repo.list_all_by_room(
                room.id
            )
            all_units.extend(units)

            failed_in_room = [
                u for u in units if u.status == "FAILED"
            ]
            failed_units.extend(failed_in_room)

            temp, hum, _, _ = (
                self._get_room_temperature_humidity(room.id)
            )

            if temp is not None:
                all_temps.append(temp)
            if hum is not None:
                all_hums.append(hum)

            room_health = "NORMAL"
            if failed_in_room:
                room_health = "WARNING"

            avg_temp, avg_hum, _, _ = (
                self._get_room_temperature_humidity(
                    room.id
                )
            )

            zones = self.zone_repo.list_all_by_room(room.id)
            for zone in zones:
                if avg_temp is not None:
                    zone_health = self._get_zone_health(
                        zone, avg_temp, avg_hum
                    )
                    if zone_health == "CRITICAL":
                        room_health = "CRITICAL"

            if room_health == "CRITICAL":
                critical_rooms.append({
                    "room_id": str(room.id),
                    "room_name": room.name,
                    "health": "CRITICAL",
                    "failed_units": len(failed_in_room),
                })

            active_in_room = [
                u for u in units if u.status == "ACTIVE"
            ]
            room_summaries.append({
                "room_id": str(room.id),
                "room_name": room.name,
                "health": room_health,
                "temperature": avg_temp,
                "humidity": avg_hum,
                "cooling_capacity_kw": sum(
                    u.cooling_capacity_kw
                    for u in active_in_room
                ),
                "active_units": len(active_in_room),
                "total_units": len(units),
                "failed_units": len(failed_in_room),
            })

        avg_dc_temp = (
            round(sum(all_temps) / len(all_temps), 1)
            if all_temps
            else None
        )
        avg_dc_hum = (
            round(sum(all_hums) / len(all_hums), 1)
            if all_hums
            else None
        )

        active_all = [
            u for u in all_units if u.status == "ACTIVE"
        ]

        failed_unit_details = [
            {
                "unit_id": str(u.id),
                "name": u.name,
                "room_id": str(u.room_id),
                "type": u.type,
            }
            for u in failed_units
        ]

        return {
            "datacenter_id": str(dc.id),
            "datacenter_name": dc.name,
            "average_temperature": avg_dc_temp,
            "average_humidity": avg_dc_hum,
            "critical_rooms": critical_rooms,
            "failed_cooling_units": failed_unit_details,
            "total_cooling_capacity_kw": sum(
                u.cooling_capacity_kw for u in active_all
            ),
            "active_cooling_units": len(active_all),
            "total_cooling_units": len(all_units),
            "room_count": len(all_rooms),
            "room_summaries": room_summaries,
        }
