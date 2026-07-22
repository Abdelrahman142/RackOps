import math
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.collectors.base import HealthStatus
from app.collectors.registry import (
    get_collector,
    list_collector_types,
)
from app.repositories.health_check import (
    HealthCheckRepository,
)
from app.repositories.metric_data import (
    MetricDataRepository,
)
from app.repositories.metric_definition import (
    MetricDefinitionRepository,
)
from app.repositories.monitoring_target import (
    MonitoringTargetRepository,
)
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_COLLECTOR_TYPES = {
    "SNMP",
    "PROMETHEUS",
    "AGENT",
    "API",
}

VALID_TARGET_STATUSES = {
    "PENDING",
    "ACTIVE",
    "WARNING",
    "ERROR",
    "DISABLED",
}

VALID_HEALTH_STATUSES = {
    "UP",
    "DOWN",
    "WARNING",
    "UNKNOWN",
}

VALID_METRIC_CATEGORIES = {
    "CPU",
    "MEMORY",
    "DISK",
    "NETWORK",
    "POWER",
    "TEMPERATURE",
    "HUMIDITY",
    "OTHER",
}

CPU_WARNING_THRESHOLD = 90.0
MEMORY_WARNING_THRESHOLD = 90.0


class MonitoringService:
    def __init__(self, db: Session):
        self.db = db
        self.target_repo = MonitoringTargetRepository(db)
        self.definition_repo = MetricDefinitionRepository(
            db
        )
        self.metric_repo = MetricDataRepository(db)
        self.health_repo = HealthCheckRepository(db)

    def _serialize_target(self, target) -> dict:
        return {
            "id": str(target.id),
            "company_id": str(target.company_id),
            "device_id": str(target.device_id),
            "enabled": target.enabled,
            "collector_type": target.collector_type,
            "endpoint": target.endpoint,
            "port": target.port,
            "interval_seconds": target.interval_seconds,
            "status": target.status,
            "last_check_at": (
                target.last_check_at.isoformat()
                if target.last_check_at
                else None
            ),
            "created_at": target.created_at.isoformat(),
            "updated_at": target.updated_at.isoformat(),
        }

    def _serialize_definition(self, defn) -> dict:
        return {
            "id": str(defn.id),
            "name": defn.name,
            "metric_key": defn.metric_key,
            "unit": defn.unit,
            "description": defn.description,
            "category": defn.category,
            "created_at": defn.created_at.isoformat(),
            "updated_at": defn.updated_at.isoformat(),
        }

    def _serialize_metric(self, metric) -> dict:
        return {
            "id": str(metric.id),
            "company_id": str(metric.company_id),
            "device_id": str(metric.device_id),
            "target_id": str(metric.target_id),
            "metric_definition_id": str(
                metric.metric_definition_id
            ),
            "value": metric.value,
            "timestamp": metric.timestamp.isoformat(),
            "created_at": metric.created_at.isoformat(),
        }

    def _serialize_health(self, check) -> dict:
        return {
            "id": str(check.id),
            "company_id": str(check.company_id),
            "device_id": str(check.device_id),
            "status": check.status,
            "response_time_ms": check.response_time_ms,
            "checked_at": check.checked_at.isoformat(),
            "created_at": check.created_at.isoformat(),
        }

    # --- Monitoring Target Methods ---

    def create_target(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        enabled: bool = True,
        collector_type: str = "AGENT",
        endpoint: str | None = None,
        port: int | None = None,
        interval_seconds: int = 60,
    ) -> dict:
        if collector_type not in VALID_COLLECTOR_TYPES:
            raise ValidationException(
                detail=(
                    f"Invalid collector_type: "
                    f"{collector_type}. Must be one of: "
                    f"{', '.join(sorted(VALID_COLLECTOR_TYPES))}"
                )
            )

        collector = get_collector(collector_type)
        if collector:
            if not collector.validate_config(
                endpoint, port
            ):
                raise ValidationException(
                    detail=(
                        f"Invalid configuration for "
                        f"{collector_type} collector"
                    )
                )

        existing = self.target_repo.get_by_device(
            company_id, device_id
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A monitoring target already exists "
                    "for this device"
                )
            )

        target = self.target_repo.create(
            company_id=company_id,
            device_id=device_id,
            enabled=enabled,
            collector_type=collector_type,
            endpoint=endpoint,
            port=port,
            interval_seconds=interval_seconds,
            status="PENDING" if enabled else "DISABLED",
        )

        self.db.commit()
        self.db.refresh(target)

        return self._serialize_target(target)

    def get_target(
        self,
        company_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> dict:
        target = (
            self.target_repo.get_active_by_company_and_id(
                company_id, target_id
            )
        )

        if not target:
            raise NotFoundException(
                detail="Monitoring target not found"
            )

        return self._serialize_target(target)

    def list_targets(
        self,
        company_id: uuid.UUID,
        enabled: bool | None = None,
        collector_type: str | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if collector_type is not None:
            if collector_type not in VALID_COLLECTOR_TYPES:
                raise ValidationException(
                    detail=(
                        "Invalid collector_type filter: "
                        f"{collector_type}"
                    )
                )

        if status is not None:
            if status not in VALID_TARGET_STATUSES:
                raise ValidationException(
                    detail=(
                        f"Invalid status filter: {status}"
                    )
                )

        items, total = (
            self.target_repo.list_by_company(
                company_id=company_id,
                enabled=enabled,
                collector_type=collector_type,
                status=status,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                size=size,
            )
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "targets": [
                self._serialize_target(t) for t in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def update_target(
        self,
        company_id: uuid.UUID,
        target_id: uuid.UUID,
        enabled: bool | None = None,
        collector_type: str | None = None,
        endpoint: str | None = None,
        port: int | None = None,
        interval_seconds: int | None = None,
        status: str | None = None,
    ) -> dict:
        target = (
            self.target_repo.get_active_by_company_and_id(
                company_id, target_id
            )
        )

        if not target:
            raise NotFoundException(
                detail="Monitoring target not found"
            )

        if collector_type is not None:
            if collector_type not in VALID_COLLECTOR_TYPES:
                raise ValidationException(
                    detail=(
                        f"Invalid collector_type: "
                        f"{collector_type}"
                    )
                )

        if status is not None:
            if status not in VALID_TARGET_STATUSES:
                raise ValidationException(
                    detail=f"Invalid status: {status}"
                )

        self.target_repo.update(
            target,
            enabled=enabled,
            collector_type=collector_type,
            endpoint=endpoint,
            port=port,
            interval_seconds=interval_seconds,
            status=status,
        )

        self.db.commit()
        self.db.refresh(target)

        return self._serialize_target(target)

    def delete_target(
        self,
        company_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> dict:
        target = (
            self.target_repo.get_active_by_company_and_id(
                company_id, target_id
            )
        )

        if not target:
            raise NotFoundException(
                detail="Monitoring target not found"
            )

        self.target_repo.soft_delete(target)
        self.db.commit()

        return {
            "message": (
                "Monitoring target deleted successfully"
            )
        }

    # --- Metric Definition Methods ---

    def create_definition(
        self,
        name: str,
        metric_key: str,
        unit: str | None = None,
        description: str | None = None,
        category: str = "OTHER",
    ) -> dict:
        if category not in VALID_METRIC_CATEGORIES:
            raise ValidationException(
                detail=(
                    f"Invalid category: {category}. "
                    "Must be one of: "
                    f"{', '.join(sorted(VALID_METRIC_CATEGORIES))}"
                )
            )

        existing = (
            self.definition_repo.get_by_metric_key(
                metric_key
            )
        )
        if existing:
            raise DuplicateException(
                detail=(
                    "A metric definition with this "
                    "metric_key already exists"
                )
            )

        defn = self.definition_repo.create(
            name=name,
            metric_key=metric_key,
            unit=unit,
            description=description,
            category=category,
        )

        self.db.commit()
        self.db.refresh(defn)

        return self._serialize_definition(defn)

    def get_definition(
        self,
        definition_id: uuid.UUID,
    ) -> dict:
        defn = self.definition_repo.get_by_id(
            definition_id
        )

        if not defn:
            raise NotFoundException(
                detail="Metric definition not found"
            )

        return self._serialize_definition(defn)

    def list_definitions(
        self,
        category: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        if category is not None:
            if category not in VALID_METRIC_CATEGORIES:
                raise ValidationException(
                    detail=(
                        "Invalid category filter: "
                        f"{category}"
                    )
                )

        items, total = (
            self.definition_repo.list_by_category(
                category=category,
                page=page,
                size=size,
            )
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "definitions": [
                self._serialize_definition(d)
                for d in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    # --- Metric Data Methods ---

    def store_metric(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        target_id: uuid.UUID,
        metric_definition_id: uuid.UUID,
        value: float,
        timestamp: datetime,
    ) -> dict:
        target = (
            self.target_repo.get_active_by_company_and_id(
                company_id, target_id
            )
        )
        if not target:
            raise NotFoundException(
                detail="Monitoring target not found"
            )

        defn = self.definition_repo.get_by_id(
            metric_definition_id
        )
        if not defn:
            raise NotFoundException(
                detail="Metric definition not found"
            )

        if target.company_id != company_id:
            raise ValidationException(
                detail=(
                    "Target does not belong to this "
                    "company"
                )
            )

        metric = self.metric_repo.create(
            company_id=company_id,
            device_id=device_id,
            target_id=target_id,
            metric_definition_id=metric_definition_id,
            value=value,
            timestamp=timestamp,
        )

        self.db.commit()
        self.db.refresh(metric)

        return self._serialize_metric(metric)

    def list_device_metrics(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        metric_definition_id: uuid.UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        size: int = 100,
    ) -> dict:
        items, total = self.metric_repo.list_by_device(
            company_id=company_id,
            device_id=device_id,
            metric_definition_id=metric_definition_id,
            start_time=start_time,
            end_time=end_time,
            page=page,
            size=size,
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "metrics": [
                self._serialize_metric(m) for m in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def get_latest_metrics(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> dict:
        latest = (
            self.metric_repo.get_latest_by_device(
                company_id, device_id
            )
        )

        return {
            "device_id": str(device_id),
            "metrics": [
                {
                    "metric_key": (
                        self.definition_repo.get_by_id(
                            m.metric_definition_id
                        ).metric_key
                        if self.definition_repo.get_by_id(
                            m.metric_definition_id
                        )
                        else str(
                            m.metric_definition_id
                        )
                    ),
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in latest
            ],
        }

    def get_device_health(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> dict:
        latest = self.health_repo.get_latest_by_device(
            company_id, device_id
        )

        if not latest:
            return {
                "device_id": str(device_id),
                "status": "UNKNOWN",
                "response_time_ms": None,
                "checked_at": None,
            }

        return self._serialize_health(latest)

    def list_device_health_checks(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        size: int = 100,
    ) -> dict:
        items, total = (
            self.health_repo.list_by_device(
                company_id=company_id,
                device_id=device_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                page=page,
                size=size,
            )
        )

        pages = math.ceil(total / size) if total > 0 else 0

        return {
            "health_checks": [
                self._serialize_health(h) for h in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    # --- Health Calculation Engine ---

    def evaluate_device_health(
        self,
        company_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> str:
        latest = self.health_repo.get_latest_by_device(
            company_id, device_id
        )

        if not latest:
            return "UNKNOWN"

        if latest.status == "DOWN":
            return "DOWN"

        if latest.status == "WARNING":
            return "WARNING"

        if latest.status == "UP":
            cpu_avg = (
                self.metric_repo.get_average_by_device_metric_key(  # noqa: E501
                    company_id,
                    device_id,
                    "cpu_usage_percent",
                )
            )

            if (
                cpu_avg is not None
                and cpu_avg >= CPU_WARNING_THRESHOLD
            ):
                return "WARNING"

            mem_avg = (
                self.metric_repo.get_average_by_device_metric_key(  # noqa: E501
                    company_id,
                    device_id,
                    "memory_usage_percent",
                )
            )

            if (
                mem_avg is not None
                and mem_avg >= MEMORY_WARNING_THRESHOLD
            ):
                return "WARNING"

            return "UP"

        return latest.status

    # --- Collector Methods ---

    def run_health_check(
        self,
        company_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> dict:
        target = (
            self.target_repo.get_active_by_company_and_id(
                company_id, target_id
            )
        )

        if not target:
            raise NotFoundException(
                detail="Monitoring target not found"
            )

        collector = get_collector(target.collector_type)

        if not collector:
            health_status = HealthStatus(
                status="UNKNOWN",
                message=(
                    "No collector available for type: "
                    f"{target.collector_type}"
                ),
            )
        else:
            health_status = collector.check_health(
                target.endpoint, target.port
            )

        check = self.health_repo.create(
            company_id=company_id,
            device_id=target.device_id,
            status=health_status.status,
            response_time_ms=health_status.response_time_ms,
        )

        self.target_repo.update(
            target,
            status=health_status.status,
            last_check_at=check.checked_at,
        )

        self.db.commit()
        self.db.refresh(check)

        return self._serialize_health(check)

    def run_metric_collection(
        self,
        company_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> list[dict]:
        target = (
            self.target_repo.get_active_by_company_and_id(
                company_id, target_id
            )
        )

        if not target:
            raise NotFoundException(
                detail="Monitoring target not found"
            )

        if not target.enabled:
            raise ValidationException(
                detail=(
                    "Cannot collect from disabled target"
                )
            )

        collector = get_collector(target.collector_type)

        if not collector:
            return []

        metric_keys = collector.supported_metrics
        now = datetime.utcnow()

        collected = collector.collect(
            target.endpoint,
            target.port,
            metric_keys,
        )

        stored = []
        for cm in collected:
            defn = (
                self.definition_repo.get_by_metric_key(
                    cm.metric_key
                )
            )

            if not defn:
                defn = self.definition_repo.create(
                    name=cm.metric_key.replace(
                        "_", " "
                    ).title(),
                    metric_key=cm.metric_key,
                    unit=cm.unit,
                    category=self._categorize_metric(
                        cm.metric_key
                    ),
                )
                self.db.flush()

            metric = self.metric_repo.create(
                company_id=company_id,
                device_id=target.device_id,
                target_id=target.id,
                metric_definition_id=defn.id,
                value=cm.value,
                timestamp=now,
            )

            stored.append(self._serialize_metric(metric))

        self.target_repo.update(
            target,
            status="ACTIVE",
            last_check_at=now,
        )

        self.db.commit()

        return stored

    def get_collector_info(self) -> list[dict]:
        result = []
        for ct in list_collector_types():
            collector = get_collector(ct)
            if collector:
                result.append({
                    "collector_type": collector.collector_type,
                    "available": True,
                    "version": collector.version,
                    "supported_metrics": (
                        collector.supported_metrics
                    ),
                })
        return result

    def _categorize_metric(
        self, metric_key: str
    ) -> str:
        if "cpu" in metric_key or "load" in metric_key:
            return "CPU"
        if "memory" in metric_key or "swap" in metric_key:
            return "MEMORY"
        if "disk" in metric_key:
            return "DISK"
        if "network" in metric_key or "if_" in metric_key:
            return "NETWORK"
        if "power" in metric_key:
            return "POWER"
        if "temperature" in metric_key:
            return "TEMPERATURE"
        return "OTHER"

    # --- Dashboard Methods ---

    def get_datacenter_monitoring_summary(
        self,
        company_id: uuid.UUID,
        datacenter_id: uuid.UUID,
    ) -> dict:
        from app.models.building import Building
        from app.models.datacenter import DataCenter
        from app.models.device import Device
        from app.models.floor import Floor
        from app.models.rack import Rack
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
            all_devices = []
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
                all_devices = []
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

                if not room_ids:
                    all_devices = []
                else:
                    racks = (
                        self.db.query(Rack)
                        .filter(
                            Rack.room_id.in_(room_ids),
                            Rack.deleted_at.is_(None),
                        )
                        .all()
                    )
                    rack_ids = [rk.id for rk in racks]

                    if not rack_ids:
                        all_devices = []
                    else:
                        all_devices = (
                            self.db.query(Device)
                            .filter(
                                Device.rack_id.in_(
                                    rack_ids
                                ),
                                Device.deleted_at.is_(
                                    None
                                ),
                            )
                            .all()
                        )

        device_ids = [d.id for d in all_devices]

        online = 0
        offline = 0
        warning = 0
        unknown = 0

        for did in device_ids:
            health = self.evaluate_device_health(
                company_id, did
            )
            if health == "UP":
                online += 1
            elif health == "DOWN":
                offline += 1
            elif health == "WARNING":
                warning += 1
            else:
                unknown += 1

        avg_cpu = None
        avg_memory = None

        if device_ids:
            avg_cpu = self.metric_repo.get_average_for_devices(  # noqa: E501
                company_id,
                device_ids,
                "cpu_usage_percent",
            )
            avg_memory = self.metric_repo.get_average_for_devices(  # noqa: E501
                company_id,
                device_ids,
                "memory_usage_percent",
            )

        device_summaries = []
        for device in all_devices:
            health = self.evaluate_device_health(
                company_id, device.id
            )
            device_cpu = (
                self.metric_repo.get_average_by_device_metric_key(  # noqa: E501
                    company_id,
                    device.id,
                    "cpu_usage_percent",
                )
            )
            device_mem = (
                self.metric_repo.get_average_by_device_metric_key(  # noqa: E501
                    company_id,
                    device.id,
                    "memory_usage_percent",
                )
            )
            device_summaries.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "health_status": health,
                "cpu_usage": device_cpu,
                "memory_usage": device_mem,
            })

        return {
            "datacenter_id": str(dc.id),
            "datacenter_name": dc.name,
            "total_devices": len(all_devices),
            "online_devices": online,
            "offline_devices": offline,
            "warning_devices": warning,
            "unknown_devices": unknown,
            "average_cpu": avg_cpu,
            "average_memory": avg_memory,
            "device_summaries": device_summaries,
        }
