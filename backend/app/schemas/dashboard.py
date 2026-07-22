from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EntityCount(BaseModel):
    datacenters: int
    buildings: int
    floors: int
    rooms: int
    racks: int
    devices: int
    ups_systems: int
    pdus: int
    cooling_units: int
    sensors: int
    network_interfaces: int
    physical_connections: int


class HealthSummary(BaseModel):
    total_checks: int
    healthy: int
    warning: int
    critical: int
    unknown: int


class PowerUsageSummary(BaseModel):
    total_capacity_kw: float
    total_actual_kw: float
    utilization_percent: float | None


class RackPowerDetail(BaseModel):
    rack_id: UUID
    rack_name: str
    rack_code: str
    room_name: str | None
    power_capacity_kw: float | None
    current_power_usage_kw: float | None


class PowerDashboard(BaseModel):
    ups_count: int
    pdu_count: int
    total_ups_capacity_kva: float
    total_rack_power_capacity_kw: float | None
    total_rack_power_usage_kw: float | None
    rack_utilization_percent: float | None
    rack_power_details: list[RackPowerDetail]


class CoolingDashboard(BaseModel):
    total_cooling_units: int
    active_units: int
    inactive_units: int
    total_cooling_capacity_kw: float | None
    zone_count: int
    sensor_count: int
    avg_temperature: float | None
    avg_humidity: float | None
    zones_over_temp: int


class NetworkDashboard(BaseModel):
    total_interfaces: int
    total_connections: int
    total_vlans: int
    total_subnets: int
    total_ip_addresses: int
    interfaces_up: int
    interfaces_down: int


class CapacityOverview(BaseModel):
    total_rack_power_capacity_kw: float | None
    total_rack_power_usage_kw: float | None
    total_cooling_capacity_kw: float | None
    total_weight_capacity_kg: float | None
    total_weight_current_kg: float | None
    power_utilization_percent: float | None
    weight_utilization_percent: float | None
    rack_space_used_units: int
    rack_space_total_units: int
    rack_space_utilization_percent: float | None


class CapacityForecast(BaseModel):
    days_ahead: int
    projected_power_usage_kw: float
    projected_power_capacity_kw: float
    projected_power_exhaustion_days: int | None
    projected_rack_space_utilization_percent: float | None
    projected_rack_space_exhaustion_days: int | None


class PowerTrendPoint(BaseModel):
    recorded_at: datetime
    avg_cpu_percent: float | None
    avg_memory_percent: float | None
    device_count: int


class AlertSummary(BaseModel):
    active_alerts: int
    critical_alerts: int
    warning_alerts: int
    open_incidents: int
    active_maintenance_windows: int


class DashboardOverview(BaseModel):
    entity_counts: EntityCount
    health_summary: HealthSummary | None
    power_summary: PowerUsageSummary | None
    alert_summary: AlertSummary | None
