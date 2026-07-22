import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base
from app.database.session import SessionLocal
from app.dependencies.auth import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def owner_data():
    uid = uuid.uuid4().hex[:8]
    return {
        "company_name": f"TestCo-{uid}",
        "company_email": f"owner-{uid}@test.com",
        "name": "Test Owner",
        "email": f"owner-{uid}@test.com",
        "password": "testpass123",
        "country": "US",
    }


@pytest.fixture
def owner_token(client, owner_data):
    client.post(
        "/api/v1/auth/register",
        json=owner_data,
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": owner_data["email"],
            "password": owner_data["password"],
        },
    )
    return resp.json()["access_token"]


@pytest.fixture
def owner_headers(owner_token):
    return {"Authorization": f"Bearer {owner_token}"}


@pytest.fixture
def admin_headers(client, owner_token):
    uid = uuid.uuid4().hex[:8]
    resp = client.post(
        "/api/v1/users",
        json={
            "name": "Test Admin",
            "email": f"admin-{uid}@test.com",
            "password": "testpass123",
            "role": "ADMIN",
        },
        headers={
            "Authorization": f"Bearer {owner_token}"
        },
    )
    admin_email = resp.json()["email"]
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": admin_email,
            "password": "testpass123",
        },
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def engineer_headers(client, owner_token):
    uid = uuid.uuid4().hex[:8]
    resp = client.post(
        "/api/v1/users",
        json={
            "name": "Test Engineer",
            "email": f"eng-{uid}@test.com",
            "password": "testpass123",
            "role": "ENGINEER",
        },
        headers={
            "Authorization": f"Bearer {owner_token}"
        },
    )
    eng_email = resp.json()["email"]
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": eng_email,
            "password": "testpass123",
        },
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers(client, owner_token):
    uid = uuid.uuid4().hex[:8]
    resp = client.post(
        "/api/v1/users",
        json={
            "name": "Test Viewer",
            "email": f"viewer-{uid}@test.com",
            "password": "testpass123",
            "role": "VIEWER",
        },
        headers={
            "Authorization": f"Bearer {owner_token}"
        },
    )
    viewer_email = resp.json()["email"]
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_email,
            "password": "testpass123",
        },
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dc_payload():
    return {
        "name": "US-East-1",
        "code": "USE1",
        "country": "United States",
        "city": "New York",
        "address": "123 Data Center Blvd",
        "timezone": "America/New_York",
        "status": "ACTIVE",
        "description": "Primary US East facility",
        "latitude": 40.7128,
        "longitude": -74.0060,
    }


def create_dc(client, headers, overrides=None):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"DC-{uid}",
        "code": f"DC{uid[:4].upper()}",
        "country": "US",
        "city": "Dallas",
        "address": "456 Server St",
        "timezone": "America/Chicago",
        "status": "ACTIVE",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/datacenters",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_building(
    client, headers, datacenter_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Building-{uid}",
        "code": f"BLD{uid[:4].upper()}",
        "address": "123 Main St",
        "status": "ACTIVE",
        "number_of_floors": 3,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/datacenters/{datacenter_id}/buildings",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_floor(
    client, headers, building_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    floor_num = int(uid[:2], 16) % 99 + 1
    payload = {
        "name": f"Floor-{uid}",
        "code": f"FLR{uid[:4].upper()}",
        "floor_number": floor_num,
        "status": "ACTIVE",
        "total_area_sqm": 500.0,
        "max_power_capacity_kw": 100.0,
        "max_cooling_capacity_kw": 80.0,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/buildings/{building_id}/floors",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_room(
    client, headers, floor_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Room-{uid}",
        "code": f"RM{uid[:4].upper()}",
        "room_type": "SERVER_ROOM",
        "status": "ACTIVE",
        "area_sqm": 100.0,
        "height_meters": 3.0,
        "max_rack_capacity": 10,
        "max_power_capacity_kw": 50.0,
        "max_cooling_capacity_kw": 40.0,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/floors/{floor_id}/rooms",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_rack(
    client, headers, room_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Rack-{uid}",
        "code": f"RK{uid[:4].upper()}",
        "rack_type": "SERVER_RACK",
        "status": "ACTIVE",
        "height_units": 42,
        "width_mm": 600.0,
        "depth_mm": 1000.0,
        "max_weight_kg": 800.0,
        "current_weight_kg": 200.0,
        "power_capacity_kw": 10.0,
        "current_power_usage_kw": 3.0,
        "cooling_capacity_kw": 8.0,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/rooms/{room_id}/racks",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_device(
    client, headers, rack_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Device-{uid}",
        "hostname": f"host-{uid}.local",
        "device_type": "SERVER",
        "status": "ACTIVE",
        "vendor": "Dell",
        "model": "PowerEdge R750",
        "serial_number": f"SN-{uid}",
        "asset_tag": f"AT-{uid}",
        "rack_unit_height": 1,
        "front_or_rear": "FRONT",
        "ip_address": "192.168.1.100",
        "management_ip": "10.0.0.100",
        "operating_system": "Ubuntu 22.04 LTS",
        "cpu": "2x Intel Xeon Gold 6348",
        "memory_gb": 256,
        "storage_gb": 2000,
        "power_consumption_watt": 750,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/racks/{rack_id}/devices",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_ups(
    client, headers, room_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"UPS-{uid}",
        "model": "Smart-UPS 3000",
        "manufacturer": "APC",
        "serial_number": f"UPS-SN-{uid}",
        "status": "ACTIVE",
        "capacity_kva": 3.0,
        "battery_capacity_minutes": 15,
        "input_voltage": 208.0,
        "output_voltage": 208.0,
        "efficiency_percent": 95.0,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/rooms/{room_id}/ups",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_pdu(
    client, headers, room_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"PDU-{uid}",
        "model": "Metered PDU",
        "manufacturer": "APC",
        "serial_number": f"PDU-SN-{uid}",
        "status": "ACTIVE",
        "total_capacity_amp": 30.0,
        "current_usage_amp": 5.0,
        "phase_type": "SINGLE",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/rooms/{room_id}/pdus",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_power_feed(
    client, headers, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "source_type": "UPS",
        "source_id": "",
        "destination_type": "PDU",
        "destination_id": "",
        "voltage": 208.0,
        "amp_rating": 30.0,
        "status": "ACTIVE",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/power-feeds",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_cooling_unit(
    client, headers, room_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"CRAC-{uid}",
        "manufacturer": "Liebert",
        "model": "DFS",
        "serial_number": f"CRAC-SN-{uid}",
        "type": "CRAC",
        "status": "ACTIVE",
        "cooling_capacity_kw": 10.0,
        "airflow_cfm": 2000.0,
        "power_consumption_kw": 3.5,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/rooms/{room_id}/cooling-units",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_zone(
    client, headers, room_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Zone-{uid}",
        "description": "Monitoring zone",
        "target_temperature_min": 18.0,
        "target_temperature_max": 27.0,
        "target_humidity_min": 30.0,
        "target_humidity_max": 60.0,
        "status": "ACTIVE",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/rooms/{room_id}/zones",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_sensor(
    client, headers, zone_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Sensor-{uid}",
        "sensor_type": "TEMPERATURE",
        "status": "ACTIVE",
        "location_description": "Rack Row A",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/zones/{zone_id}/sensors",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_interface(
    client, headers, device_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"eth0-{uid}",
        "interface_type": "ETHERNET",
        "status": "UP",
        "mac_address": f"00:11:22:33:{uid[:2]}:{uid[2:4]}",
        "ip_address": f"10.0.{int(uid[:2], 16)}.{int(uid[2:4], 16)}",
        "speed_mbps": 10000,
        "description": "Primary NIC",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/devices/{device_id}/interfaces",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_connection(
    client, headers, overrides=None
):
    payload = {
        "source_interface_id": "",
        "destination_interface_id": "",
        "connection_type": "COPPER",
        "cable_type": "CAT6A",
        "length_meters": 5,
        "status": "ACTIVE",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/connections",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_vlan(
    client, headers, datacenter_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    vlan_num = int(uid[:3], 16) % 4093 + 1
    payload = {
        "name": f"VLAN-{uid}",
        "vlan_id": vlan_num,
        "description": "Test VLAN",
        "status": "ACTIVE",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/datacenters/{datacenter_id}/vlans",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_subnet(
    client, headers, vlan_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    octet = int(uid[:2], 16) % 254 + 1
    payload = {
        "network_address": f"10.{octet}.0.0",
        "cidr": 24,
        "gateway": f"10.{octet}.0.1",
        "description": "Test subnet",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/vlans/{vlan_id}/subnets",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_ip(
    client, headers, subnet_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "address": f"10.10.{int(uid[:2], 16) % 254}.{int(uid[2:4], 16) % 254 + 1}",
        "status": "AVAILABLE",
        "description": "Test IP",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/subnets/{subnet_id}/ips",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_monitoring_target(
    client, headers, device_id, overrides=None
):
    payload = {
        "enabled": True,
        "collector_type": "AGENT",
        "interval_seconds": 60,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/devices/{device_id}/monitoring",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_metric_definition(
    client, headers, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"CPU Usage {uid}",
        "metric_key": f"cpu_usage_{uid}",
        "unit": "%",
        "description": "CPU usage percentage",
        "category": "CPU",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/metric-definitions",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_health_check(
    client, headers, device_id, overrides=None
):
    payload = {
        "status": "UP",
        "response_time_ms": 15.0,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/devices/{device_id}/health",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_alert_rule(
    client, headers, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Rule-{uid}",
        "metric_key": f"cpu_usage_{uid}",
        "condition": "GREATER_THAN",
        "threshold_value": 90.0,
        "severity": "WARNING",
        "enabled": True,
        "evaluation_interval_seconds": 300,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/alert-rules",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_maintenance_window(
    client, headers, overrides=None
):
    from datetime import datetime, timedelta

    uid = uuid.uuid4().hex[:8]
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=2)
    payload = {
        "name": f"Maintenance-{uid}",
        "description": "Scheduled maintenance",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/maintenance-windows",
        json=payload,
        headers=headers,
    )
    return resp.json()


# --- Automation Helpers ---


def create_automation_job(
    client, headers, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Job-{uid}",
        "job_type": "COMMAND",
        "description": "Test automation job",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/automation/jobs",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_device_connector(
    client, headers, device_id, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "connector_type": "SSH",
        "hostname": f"10.0.{int(uid[:2], 16) % 254}.{int(uid[2:4], 16) % 254 + 1}",
        "port": 22,
        "username": "admin",
        "password": "secret123",
        "enabled": True,
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/devices/{device_id}/connectors",
        json=payload,
        headers=headers,
    )
    return resp.json()


def create_backup(
    client, headers, device_id, overrides=None
):
    payload = {
        "device_id": device_id,
        "backup_type": "CONFIG",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        f"/api/v1/devices/{device_id}/backups",
        json=payload,
        headers=headers,
    )
    return resp.json()
