from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.building import Building
from app.models.cooling_unit import CoolingUnit
from app.models.datacenter import DataCenter
from app.models.device import Device
from app.models.environmental_zone import EnvironmentalZone
from app.models.floor import Floor
from app.models.incident import AlertIncident
from app.models.ip_address import IPAddress
from app.models.maintenance_window import MaintenanceWindow
from app.models.metric_data import MetricData
from app.models.network_interface import NetworkInterface
from app.models.physical_connection import PhysicalConnection
from app.models.pdu import PDU
from app.models.rack import Rack
from app.models.room import Room
from app.models.sensor import Sensor
from app.models.subnet import Subnet
from app.models.ups import UPS
from app.models.health_check import HealthCheck
from app.models.metric_definition import MetricDefinition
from app.models.vlan import VLAN


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_entity_counts(self, company_id: UUID) -> dict:
        results = {}
        for label, model in [
            ("datacenters", DataCenter),
            ("buildings", Building),
            ("floors", Floor),
            ("rooms", Room),
            ("racks", Rack),
            ("devices", Device),
            ("ups_systems", UPS),
            ("pdus", PDU),
            ("cooling_units", CoolingUnit),
            ("sensors", Sensor),
            ("network_interfaces", NetworkInterface),
            ("physical_connections", PhysicalConnection),
        ]:
            stmt = select(func.count()).select_from(model).where(
                model.company_id == company_id,
                model.deleted_at.is_(None) if hasattr(model, 'deleted_at') else True,
            )
            results[label] = self.db.execute(stmt).scalar_one()
        return results

    def get_health_summary(self, company_id: UUID) -> dict:
        stmt = (
            select(HealthCheck.status, func.count())
            .where(HealthCheck.company_id == company_id)
            .group_by(HealthCheck.status)
        )
        rows = self.db.execute(stmt).all()
        status_map = {row[0]: row[1] for row in rows}
        return {
            "total_checks": sum(status_map.values()),
            "healthy": status_map.get("HEALTHY", 0),
            "warning": status_map.get("WARNING", 0),
            "critical": status_map.get("CRITICAL", 0),
            "unknown": status_map.get("UNKNOWN", 0),
        }

    def get_power_usage_summary(self, company_id: UUID) -> dict:
        stmt = select(
            func.coalesce(func.sum(Rack.power_capacity_kw), 0.0),
            func.coalesce(func.sum(Rack.current_power_usage_kw), 0.0),
        ).where(
            Rack.company_id == company_id,
            Rack.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).one()
        capacity, usage = float(row[0]), float(row[1])
        utilization = (usage / capacity * 100) if capacity > 0 else None
        return {
            "total_capacity_kw": capacity,
            "total_actual_kw": usage,
            "utilization_percent": utilization,
        }

    def get_rack_power_details(self, company_id: UUID) -> list[dict]:
        stmt = (
            select(Rack.id, Rack.name, Rack.code,
                   Rack.power_capacity_kw, Rack.current_power_usage_kw,
                   Room.name.label("room_name"))
            .join(Room, Rack.room_id == Room.id)
            .where(
                Rack.company_id == company_id,
                Rack.deleted_at.is_(None),
            )
            .order_by(Room.name, Rack.name)
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                "rack_id": r[0],
                "rack_name": r[1],
                "rack_code": r[2],
                "room_name": r[5],
                "power_capacity_kw": r[3],
                "current_power_usage_kw": r[4],
            }
            for r in rows
        ]

    def get_cooling_dashboard(self, company_id: UUID) -> dict:
        cu_stmt = select(
            func.count(),
            func.sum(CoolingUnit.cooling_capacity_kw),
        ).where(
            CoolingUnit.company_id == company_id,
            CoolingUnit.deleted_at.is_(None),
        )
        cu_row = self.db.execute(cu_stmt).one()
        total_units = cu_row[0]
        total_capacity = float(cu_row[1]) if cu_row[1] else None

        cu_status_stmt = (
            select(CoolingUnit.status, func.count())
            .where(
                CoolingUnit.company_id == company_id,
                CoolingUnit.deleted_at.is_(None),
            )
            .group_by(CoolingUnit.status)
        )
        cu_status_rows = self.db.execute(cu_status_stmt).all()
        cu_status_map = {r[0]: r[1] for r in cu_status_rows}

        zone_stmt = select(func.count()).select_from(EnvironmentalZone).where(
            EnvironmentalZone.company_id == company_id,
        )
        zone_count = self.db.execute(zone_stmt).scalar_one()

        sensor_stmt = select(func.count()).select_from(Sensor).where(
            Sensor.company_id == company_id,
        )
        sensor_count = self.db.execute(sensor_stmt).scalar_one()

        avg_temp_stmt = select(
            func.avg(Sensor.last_value),
        ).where(
            Sensor.company_id == company_id,
            Sensor.sensor_type == "TEMPERATURE",
        )
        avg_temp = self.db.execute(avg_temp_stmt).scalar_one()

        avg_hum_stmt = select(
            func.avg(Sensor.last_value),
        ).where(
            Sensor.company_id == company_id,
            Sensor.sensor_type == "HUMIDITY",
        )
        avg_hum = self.db.execute(avg_hum_stmt).scalar_one()

        return {
            "total_cooling_units": total_units,
            "active_units": cu_status_map.get("ACTIVE", 0),
            "inactive_units": total_units - cu_status_map.get("ACTIVE", 0),
            "total_cooling_capacity_kw": total_capacity,
            "zone_count": zone_count,
            "sensor_count": sensor_count,
            "avg_temperature": float(avg_temp) if avg_temp else None,
            "avg_humidity": float(avg_hum) if avg_hum else None,
            "zones_over_temp": 0,
        }

    def get_network_dashboard(self, company_id: UUID) -> dict:
        ni_stmt = select(
            func.count(),
            func.sum(func.cast(NetworkInterface.status == "UP", Integer)),
            func.sum(func.cast(NetworkInterface.status == "DOWN", Integer)),
        ).where(NetworkInterface.company_id == company_id)
        ni_row = self.db.execute(ni_stmt).one()

        pc_stmt = select(func.count()).select_from(PhysicalConnection).where(
            PhysicalConnection.company_id == company_id,
        )
        pc_count = self.db.execute(pc_stmt).scalar_one()

        vlan_stmt = select(func.count()).select_from(VLAN).where(
            VLAN.company_id == company_id,
        )
        vlan_count = self.db.execute(vlan_stmt).scalar_one()

        subnet_stmt = select(func.count()).select_from(Subnet).where(
            Subnet.company_id == company_id,
        )
        subnet_count = self.db.execute(subnet_stmt).scalar_one()

        ip_stmt = select(func.count()).select_from(IPAddress).where(
            IPAddress.company_id == company_id,
        )
        ip_count = self.db.execute(ip_stmt).scalar_one()

        return {
            "total_interfaces": ni_row[0],
            "total_connections": pc_count,
            "total_vlans": vlan_count,
            "total_subnets": subnet_count,
            "total_ip_addresses": ip_count,
            "interfaces_up": int(ni_row[1]) if ni_row[1] else 0,
            "interfaces_down": int(ni_row[2]) if ni_row[2] else 0,
        }

    def get_alert_summary(self, company_id: UUID) -> dict:
        active_stmt = select(func.count()).select_from(Alert).where(
            Alert.company_id == company_id,
            Alert.status == "ACTIVE",
        )
        active_count = self.db.execute(active_stmt).scalar_one()

        crit_stmt = select(func.count()).select_from(Alert).where(
            Alert.company_id == company_id,
            Alert.severity == "CRITICAL",
            Alert.status == "ACTIVE",
        )
        crit_count = self.db.execute(crit_stmt).scalar_one()

        warn_stmt = select(func.count()).select_from(Alert).where(
            Alert.company_id == company_id,
            Alert.severity == "WARNING",
            Alert.status == "ACTIVE",
        )
        warn_count = self.db.execute(warn_stmt).scalar_one()

        inc_stmt = select(func.count()).select_from(AlertIncident).where(
            AlertIncident.company_id == company_id,
            AlertIncident.status.in_(["OPEN", "IN_PROGRESS"]),
        )
        inc_count = self.db.execute(inc_stmt).scalar_one()

        now = datetime.now(timezone.utc)
        mw_stmt = select(func.count()).select_from(MaintenanceWindow).where(
            MaintenanceWindow.company_id == company_id,
            MaintenanceWindow.start_time <= now,
            MaintenanceWindow.end_time >= now,
        )
        mw_count = self.db.execute(mw_stmt).scalar_one()

        return {
            "active_alerts": active_count,
            "critical_alerts": crit_count,
            "warning_alerts": warn_count,
            "open_incidents": inc_count,
            "active_maintenance_windows": mw_count,
        }

    def get_capacity_overview(self, company_id: UUID) -> dict:
        stmt = select(
            func.coalesce(func.sum(Rack.power_capacity_kw), 0.0),
            func.coalesce(func.sum(Rack.current_power_usage_kw), 0.0),
            func.coalesce(func.sum(Rack.max_weight_kg), 0.0),
            func.coalesce(func.sum(Rack.current_weight_kg), 0.0),
            func.coalesce(func.sum(Rack.height_units), 0),
            func.coalesce(func.sum(Rack.cooling_capacity_kw), 0.0),
        ).where(
            Rack.company_id == company_id,
            Rack.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).one()
        p_cap = float(row[0])
        p_use = float(row[1])
        w_cap = float(row[2])
        w_use = float(row[3])
        total_units = int(row[4])
        cooling_cap = float(row[5])

        used_units_stmt = select(
            func.coalesce(func.sum(Device.rack_unit_height), 0),
        ).join(Rack, Device.rack_id == Rack.id).where(
            Device.company_id == company_id,
            Device.deleted_at.is_(None),
        )
        used_units = self.db.execute(used_units_stmt).scalar_one()

        return {
            "total_rack_power_capacity_kw": p_cap if p_cap > 0 else None,
            "total_rack_power_usage_kw": p_use if p_cap > 0 else None,
            "total_cooling_capacity_kw": cooling_cap if cooling_cap > 0 else None,
            "total_weight_capacity_kg": w_cap if w_cap > 0 else None,
            "total_weight_current_kg": w_use if w_cap > 0 else None,
            "power_utilization_percent": (p_use / p_cap * 100) if p_cap > 0 else None,
            "weight_utilization_percent": (w_use / w_cap * 100) if w_cap > 0 else None,
            "rack_space_used_units": int(used_units),
            "rack_space_total_units": total_units,
            "rack_space_utilization_percent": (int(used_units) / total_units * 100) if total_units > 0 else None,
        }

    def get_capacity_forecast(self, company_id: UUID, days_ahead: int = 30) -> dict:
        import math

        now = datetime.now(timezone.utc)
        lookback = now - timedelta(days=30)

        rack_stmt = select(
            func.coalesce(func.sum(Rack.power_capacity_kw), 0.0),
            func.coalesce(func.sum(Rack.current_power_usage_kw), 0.0),
            func.coalesce(func.sum(Rack.height_units), 0),
        ).where(
            Rack.company_id == company_id,
            Rack.deleted_at.is_(None),
        )
        r_row = self.db.execute(rack_stmt).one()
        p_cap = float(r_row[0])
        p_use = float(r_row[1])
        total_units = int(r_row[2])

        growth_rate = 0.01
        projected_power = p_use * (1 + growth_rate) ** days_ahead
        power_exhaustion = None
        if p_cap > 0 and growth_rate > 0 and p_use > 0:
            remaining_ratio = p_cap / p_use
            if remaining_ratio > 1:
                power_exhaustion = int(math.log(remaining_ratio) / math.log(1 + growth_rate))

        used_units_stmt = select(
            func.coalesce(func.sum(Device.rack_unit_height), 0),
        ).join(Rack, Device.rack_id == Rack.id).where(
            Device.company_id == company_id,
            Device.deleted_at.is_(None),
        )
        used_units = self.db.execute(used_units_stmt).scalar_one()
        space_util = (int(used_units) / total_units * 100) if total_units > 0 else None
        space_exhaustion = None
        if total_units > 0 and growth_rate > 0 and int(used_units) > 0:
            remaining_units = total_units - int(used_units)
            if remaining_units > 0:
                space_exhaustion = int(math.log(total_units / int(used_units)) / math.log(1 + growth_rate * 0.5))

        return {
            "days_ahead": days_ahead,
            "projected_power_usage_kw": projected_power,
            "projected_power_capacity_kw": p_cap,
            "projected_power_exhaustion_days": power_exhaustion,
            "projected_rack_space_utilization_percent": space_util,
            "projected_rack_space_exhaustion_days": space_exhaustion,
        }

    def get_power_trends(self, company_id: UUID, days: int = 7) -> list[dict]:
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(days=days)

        stmt = (
            select(
                MetricData.timestamp,
                func.avg(MetricData.value).label("avg_value"),
                func.count(func.distinct(MetricData.device_id)).label("device_count"),
            )
            .join(MetricDefinition, MetricData.metric_definition_id == MetricDefinition.id)
            .where(
                MetricData.company_id == company_id,
                MetricData.timestamp >= lookback,
                MetricDefinition.metric_key == "CPU_UTILIZATION",
            )
            .group_by(MetricData.timestamp)
            .order_by(MetricData.timestamp)
            .limit(200)
        )
        rows = self.db.execute(stmt).all()

        return [
            {
                "recorded_at": r[0],
                "avg_cpu_percent": float(r[1]) if r[1] else None,
                "avg_memory_percent": None,
                "device_count": r[2],
            }
            for r in rows
        ]

    def get_dashboard_overview(self, company_id: UUID) -> dict:
        entity_counts = self.get_entity_counts(company_id)
        health_summary = self.get_health_summary(company_id)
        power_summary = self.get_power_usage_summary(company_id)
        alert_summary = self.get_alert_summary(company_id)
        return {
            "entity_counts": entity_counts,
            "health_summary": health_summary,
            "power_summary": power_summary,
            "alert_summary": alert_summary,
        }
