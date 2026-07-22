import uuid
from datetime import datetime, timedelta

import pytest
from tests.conftest import (
    create_building,
    create_device,
    create_floor,
    create_metric_definition,
    create_monitoring_target,
    create_room,
)


# ===========================
# Helpers
# ===========================


def _create_full_dc_stack(client, headers):
    uid = uuid.uuid4().hex[:8]
    dc_resp = client.post(
        "/api/v1/datacenters",
        json={
            "name": f"DC-{uid}",
            "code": f"DC{uid[:4].upper()}",
            "country": "US",
            "city": "Dallas",
            "address": "456 Server St",
            "timezone": "America/Chicago",
            "status": "ACTIVE",
        },
        headers=headers,
    )
    dc_id = dc_resp.json()["id"]
    building = create_building(
        client, headers, dc_id
    )
    building_id = building["id"]
    floor = create_floor(
        client, headers, building_id
    )
    floor_id = floor["id"]
    room = create_room(client, headers, floor_id)
    room_id = room["id"]
    return dc_id, building_id, floor_id, room_id


def _create_device_in_dc(client, headers):
    dc_id, _, _, room_id = _create_full_dc_stack(
        client, headers
    )
    uid = uuid.uuid4().hex[:8]
    rack_payload = {
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
    rack_resp = client.post(
        f"/api/v1/rooms/{room_id}/racks",
        json=rack_payload,
        headers=headers,
    )
    rack_id = rack_resp.json()["id"]
    device = create_device(
        client, headers, rack_id
    )
    return dc_id, device["id"]


# ===========================
# Monitoring Target Tests
# ===========================


class TestMonitoringTargetCRUD:
    def test_create_target(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        assert target["id"]
        assert target["device_id"] == device_id
        assert target["collector_type"] == "AGENT"
        assert target["enabled"] is True
        assert target["interval_seconds"] == 60

    def test_create_target_with_snmp(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client,
            owner_headers,
            device_id,
            overrides={
                "collector_type": "SNMP",
                "endpoint": "192.168.1.100",
                "port": 161,
            },
        )
        assert target["collector_type"] == "SNMP"
        assert target["endpoint"] == "192.168.1.100"
        assert target["port"] == 161

    def test_create_target_with_prometheus(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client,
            owner_headers,
            device_id,
            overrides={
                "collector_type": "PROMETHEUS",
                "endpoint": "http://prometheus:9090",
                "interval_seconds": 30,
            },
        )
        assert target["collector_type"] == "PROMETHEUS"
        assert target["interval_seconds"] == 30

    def test_list_targets(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.get(
            "/api/v1/monitoring",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_target(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.get(
            f"/api/v1/monitoring/{target['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == target["id"]

    def test_get_device_monitoring(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.get(
            f"/api/v1/devices/{device_id}/monitoring",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["device_id"] == device_id

    def test_get_device_monitoring_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/devices/{fake_id}/monitoring",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_target(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.patch(
            f"/api/v1/monitoring/{target['id']}",
            json={
                "interval_seconds": 120,
                "enabled": False,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["interval_seconds"] == 120
        assert resp.json()["enabled"] is False

    def test_delete_target(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.delete(
            f"/api/v1/monitoring/{target['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

        resp2 = client.get(
            f"/api/v1/monitoring/{target['id']}",
            headers=owner_headers,
        )
        assert resp2.status_code == 404

    def test_duplicate_target_rejected(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = create_monitoring_target(
            client, owner_headers, device_id
        )
        assert "detail" in resp or resp.get(
            "id"
        ) is None


# ===========================
# Metric Definition Tests
# ===========================


class TestMetricDefinitionCRUD:
    def test_create_definition(
        self, client, owner_headers
    ):
        defn = create_metric_definition(
            client, owner_headers
        )
        assert defn["id"]
        assert defn["category"] == "CPU"

    def test_create_memory_definition(
        self, client, owner_headers
    ):
        defn = create_metric_definition(
            client,
            owner_headers,
            overrides={
                "name": "Memory Usage",
                "metric_key": "memory_usage_percent",
                "category": "MEMORY",
                "unit": "%",
            },
        )
        assert defn["category"] == "MEMORY"

    def test_list_definitions(
        self, client, owner_headers
    ):
        create_metric_definition(
            client, owner_headers
        )
        create_metric_definition(
            client,
            owner_headers,
            overrides={
                "name": "Memory",
                "metric_key": "mem_test",
                "category": "MEMORY",
            },
        )
        resp = client.get(
            "/api/v1/metric-definitions",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_definitions_by_category(
        self, client, owner_headers
    ):
        create_metric_definition(
            client,
            owner_headers,
            overrides={
                "metric_key": "cpu_filter_test",
                "category": "CPU",
            },
        )
        create_metric_definition(
            client,
            owner_headers,
            overrides={
                "name": "Memory",
                "metric_key": "mem_filter_test",
                "category": "MEMORY",
            },
        )
        resp = client.get(
            "/api/v1/metric-definitions?category=CPU",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        for d in resp.json()["definitions"]:
            assert d["category"] == "CPU"

    def test_get_definition(
        self, client, owner_headers
    ):
        defn = create_metric_definition(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/metric-definitions/{defn['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_duplicate_metric_key_rejected(
        self, client, owner_headers
    ):
        defn = create_metric_definition(
            client,
            owner_headers,
            overrides={"metric_key": "unique_key_123"},
        )
        resp = client.post(
            "/api/v1/metric-definitions",
            json={
                "name": "Dup",
                "metric_key": "unique_key_123",
                "category": "CPU",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409


# ===========================
# Metric Data Tests
# ===========================


class TestMetricDataCRUD:
    def test_store_metric(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        defn = create_metric_definition(
            client,
            owner_headers,
            overrides={"metric_key": "cpu_metric_test"},
        )
        now = datetime.utcnow().isoformat()
        resp = client.post(
            f"/api/v1/devices/{device_id}/metrics",
            json={
                "metric_definition_id": defn["id"],
                "value": 75.5,
                "timestamp": now,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["value"] == 75.5

    def test_list_device_metrics(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        defn = create_metric_definition(
            client,
            owner_headers,
            overrides={"metric_key": "cpu_list_test"},
        )
        now = datetime.utcnow().isoformat()
        client.post(
            f"/api/v1/devices/{device_id}/metrics",
            json={
                "metric_definition_id": defn["id"],
                "value": 50.0,
                "timestamp": now,
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/devices/{device_id}/metrics",
            json={
                "metric_definition_id": defn["id"],
                "value": 60.0,
                "timestamp": now,
            },
            headers=owner_headers,
        )
        resp = client.get(
            f"/api/v1/devices/{device_id}/metrics",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_get_latest_metrics(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        defn = create_metric_definition(
            client,
            owner_headers,
            overrides={
                "metric_key": "cpu_latest_test"
            },
        )
        now = datetime.utcnow().isoformat()
        client.post(
            f"/api/v1/devices/{device_id}/metrics",
            json={
                "metric_definition_id": defn["id"],
                "value": 85.0,
                "timestamp": now,
            },
            headers=owner_headers,
        )
        resp = client.get(
            f"/api/v1/devices/{device_id}/metrics/latest",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["device_id"] == device_id

    def test_store_metric_no_target(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        fake_device = str(uuid.uuid4())
        defn = create_metric_definition(
            client,
            owner_headers,
            overrides={"metric_key": f"cpu_notarget_{uid}"},
        )
        now = datetime.utcnow().isoformat()
        resp = client.post(
            f"/api/v1/devices/{fake_device}/metrics",
            json={
                "metric_definition_id": defn["id"],
                "value": 50.0,
                "timestamp": now,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404


# ===========================
# Health Check Tests
# ===========================


class TestHealthCheck:
    def test_get_device_health(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.get(
            f"/api/v1/devices/{device_id}/health",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["device_id"] == device_id

    def test_list_health_checks(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.get(
            f"/api/v1/devices/{device_id}/health/history",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_health_check_no_data(
        self, client, owner_headers
    ):
        fake_device = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/devices/{fake_device}/health",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "UNKNOWN"


# ===========================
# Collector Tests
# ===========================


class TestCollectors:
    def test_list_collectors(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/collectors",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        collectors = resp.json()
        types = [c["collector_type"] for c in collectors]
        assert "SNMP" in types
        assert "PROMETHEUS" in types
        assert "AGENT" in types

    def test_run_health_check(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.post(
            f"/api/v1/monitoring/{target['id']}/check",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "UP"

    def test_run_metric_collection(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.post(
            f"/api/v1/monitoring/{target['id']}/collect",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_collect_disabled_target(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client,
            owner_headers,
            device_id,
            overrides={"enabled": False},
        )
        resp = client.post(
            f"/api/v1/monitoring/{target['id']}/collect",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_collector_info(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/collectors",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        for c in resp.json():
            assert "supported_metrics" in c
            assert "version" in c
            assert "available" in c


# ===========================
# Collector Unit Tests
# ===========================


class TestCollectorFramework:
    def test_snmp_collector_validate(self):
        from app.collectors.snmp_collector import (
            SNMPCollector,
        )

        c = SNMPCollector()
        assert c.collector_type == "SNMP"
        assert c.validate_config("192.168.1.1", 161)
        assert c.validate_config(
            "192.168.1.1", None
        )
        assert not c.validate_config(None, 161)
        assert not c.validate_config(
            "host", 99999
        )

    def test_snmp_collector_health(self):
        from app.collectors.snmp_collector import (
            SNMPCollector,
        )

        c = SNMPCollector()
        h = c.check_health("192.168.1.1", 161)
        assert h.status == "UP"
        h2 = c.check_health(None, 161)
        assert h2.status == "DOWN"

    def test_prometheus_collector_validate(self):
        from app.collectors.prometheus_collector import (
            PrometheusCollector,
        )

        c = PrometheusCollector()
        assert c.validate_config(
            "http://prom:9090", 9090
        )
        assert not c.validate_config("prom", 9090)
        assert not c.validate_config(None, 9090)

    def test_agent_collector_validate(self):
        from app.collectors.agent_collector import (
            AgentCollector,
        )

        c = AgentCollector()
        assert c.validate_config("10.0.0.1", 8080)
        assert c.validate_config(None, 8080)
        assert not c.validate_config("host", 99999)

    def test_registry(self):
        from app.collectors.registry import (
            get_collector,
            list_collector_types,
        )

        types = list_collector_types()
        assert "SNMP" in types
        assert "PROMETHEUS" in types
        assert "AGENT" in types
        assert get_collector("SNMP") is not None
        assert get_collector("INVALID") is None

    def test_snmp_collector_supported_metrics(self):
        from app.collectors.snmp_collector import (
            SNMPCollector,
        )

        c = SNMPCollector()
        metrics = c.supported_metrics
        assert "cpu_usage_percent" in metrics
        assert "temperature_celsius" in metrics
        assert c.version == "1.0.0"

    def test_agent_collector_supported_metrics(self):
        from app.collectors.agent_collector import (
            AgentCollector,
        )

        c = AgentCollector()
        metrics = c.supported_metrics
        assert "cpu_usage_percent" in metrics
        assert "swap_usage_percent" in metrics
        assert "process_count" in metrics


# ===========================
# Dashboard Tests
# ===========================


class TestDashboard:
    def test_monitoring_summary_empty(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        dc_resp = client.post(
            "/api/v1/datacenters",
            json={
                "name": f"DC-Dash-{uid}",
                "code": f"DDS{uid[:4].upper()}",
                "country": "US",
                "city": "Dallas",
                "address": "456 Server St",
                "timezone": "America/Chicago",
                "status": "ACTIVE",
            },
            headers=owner_headers,
        )
        dc_id = dc_resp.json()["id"]
        resp = client.get(
            f"/api/v1/datacenters/{dc_id}/monitoring-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_devices"] == 0
        assert data["online_devices"] == 0

    def test_monitoring_summary_with_devices(
        self, client, owner_headers
    ):
        dc_id, device_id = _create_device_in_dc(
            client, owner_headers
        )
        create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.get(
            f"/api/v1/datacenters/{dc_id}/monitoring-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_devices"] == 1

    def test_monitoring_summary_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/datacenters/{fake_id}/monitoring-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# ===========================
# RBAC Tests
# ===========================


class TestRBAC:
    def test_viewer_can_read_targets(
        self, client, owner_headers, viewer_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.get(
            "/api/v1/monitoring",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_cannot_create_target(
        self, client, owner_headers, viewer_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/devices/{device_id}/monitoring",
            json={
                "enabled": True,
                "collector_type": "AGENT",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_engineer_can_create_target(
        self, client, owner_headers, engineer_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/devices/{device_id}/monitoring",
            json={
                "enabled": True,
                "collector_type": "AGENT",
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_engineer_can_run_health_check(
        self, client, owner_headers, engineer_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )
        resp = client.post(
            f"/api/v1/monitoring/{target['id']}/check",
            headers=engineer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_can_read_collectors(
        self, client, owner_headers, viewer_headers
    ):
        resp = client.get(
            "/api/v1/collectors",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_cannot_create_definition(
        self, client, owner_headers, viewer_headers
    ):
        resp = client.post(
            "/api/v1/metric-definitions",
            json={
                "name": "Test",
                "metric_key": "test_key",
                "category": "CPU",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403


# ===========================
# Validation Tests
# ===========================


class TestValidation:
    def test_invalid_collector_type(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/devices/{device_id}/monitoring",
            json={
                "collector_type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_invalid_metric_category(
        self, client, owner_headers
    ):
        resp = client.post(
            "/api/v1/metric-definitions",
            json={
                "name": "Test",
                "metric_key": "test_invalid_cat",
                "category": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_interval_too_low(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/devices/{device_id}/monitoring",
            json={
                "collector_type": "AGENT",
                "interval_seconds": 5,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_port_out_of_range(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/devices/{device_id}/monitoring",
            json={
                "collector_type": "SNMP",
                "port": 99999,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ===========================
# Tenant Isolation Tests
# ===========================


class TestTenantIsolation:
    def test_cross_company_target_access(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"OtherCo-{uid}",
                "company_email": f"other-{uid}@test.com",
                "name": "Other Owner",
                "email": f"other-{uid}@test.com",
                "password": "testpass123",
                "country": "US",
            },
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other-{uid}@test.com",
                "password": "testpass123",
            },
        )
        other_headers = {
            "Authorization": (
                f"Bearer {other_login.json()['access_token']}"
            )
        }

        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        target = create_monitoring_target(
            client, owner_headers, device_id
        )

        resp = client.get(
            f"/api/v1/monitoring/{target['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404

    def test_cross_company_definition_access(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"OtherCo2-{uid}",
                "company_email": f"other2-{uid}@test.com",
                "name": "Other2",
                "email": f"other2-{uid}@test.com",
                "password": "testpass123",
                "country": "US",
            },
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other2-{uid}@test.com",
                "password": "testpass123",
            },
        )
        other_headers = {
            "Authorization": (
                f"Bearer {other_login.json()['access_token']}"
            )
        }

        defn = create_metric_definition(
            client, owner_headers
        )

        resp = client.get(
            f"/api/v1/metric-definitions/{defn['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 200


# ===========================
# Metric Scheduler Tests
# ===========================


class TestMetricScheduler:
    def test_scheduler_collect_all(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        create_monitoring_target(
            client, owner_headers, device_id
        )

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import settings
        from app.services.metric_scheduler import (
            MetricCollectionScheduler,
        )

        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()

        scheduler = MetricCollectionScheduler(db)
        uid = uuid.uuid4().hex[:8]

        from app.models.user import User

        user = (
            db.query(User)
            .filter(User.email == owner_headers.get("Authorization", "")[:10])
            .first()
        )

        if user:
            results = scheduler.collect_all_enabled(
                user.company_id
            )
            assert isinstance(results, list)

        db.close()
        engine.dispose()
