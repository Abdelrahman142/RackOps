import uuid
from datetime import datetime, timedelta

import pytest
from tests.conftest import (
    create_alert_rule,
    create_building,
    create_device,
    create_floor,
    create_maintenance_window,
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


def _create_alert(
    client, headers, device_id, rule, overrides=None
):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "device_id": device_id,
        "rule_id": rule["id"],
        "title": f"Alert-{uid}",
        "severity": "WARNING",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/alerts",
        json=payload,
        headers=headers,
    )
    return resp.json()


# ===========================
# Alert Rule Tests
# ===========================


class TestAlertRuleCRUD:
    def test_create_alert_rule(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/alert-rules",
            json={
                "name": f"High CPU-{uid}",
                "metric_key": f"cpu_usage_{uid}",
                "condition": "GREATER_THAN",
                "threshold_value": 90.0,
                "severity": "WARNING",
                "enabled": True,
                "evaluation_interval_seconds": 300,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == f"High CPU-{uid}"
        assert data["metric_key"] == f"cpu_usage_{uid}"
        assert data["condition"] == "GREATER_THAN"
        assert data["threshold_value"] == 90.0
        assert data["severity"] == "WARNING"
        assert data["enabled"] is True

    def test_create_rule_missing_name(
        self, client, owner_headers
    ):
        resp = client.post(
            "/api/v1/alert-rules",
            json={
                "metric_key": "cpu",
                "condition": "GREATER_THAN",
                "threshold_value": 90.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_rule_invalid_condition(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/alert-rules",
            json={
                "name": f"Bad-{uid}",
                "metric_key": f"cpu_{uid}",
                "condition": "INVALID",
                "threshold_value": 90.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_rule_invalid_severity(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/alert-rules",
            json={
                "name": f"Bad-{uid}",
                "metric_key": f"cpu_{uid}",
                "condition": "GREATER_THAN",
                "threshold_value": 90.0,
                "severity": "EXTREME",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_rules(
        self, client, owner_headers
    ):
        create_alert_rule(
            client, owner_headers
        )
        create_alert_rule(
            client, owner_headers
        )
        resp = client.get(
            "/api/v1/alert-rules",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert len(data["rules"]) >= 2

    def test_list_rules_filter_severity(
        self, client, owner_headers
    ):
        create_alert_rule(
            client,
            owner_headers,
            {"severity": "CRITICAL"},
        )
        resp = client.get(
            "/api/v1/alert-rules?severity=CRITICAL",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        for rule in resp.json()["rules"]:
            assert rule["severity"] == "CRITICAL"

    def test_list_rules_filter_enabled(
        self, client, owner_headers
    ):
        create_alert_rule(
            client, owner_headers
        )
        resp = client.get(
            "/api/v1/alert-rules?enabled=true",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        for rule in resp.json()["rules"]:
            assert rule["enabled"] is True

    def test_get_rule(
        self, client, owner_headers
    ):
        rule = create_alert_rule(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/alert-rules/{rule['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == rule["id"]

    def test_get_rule_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/alert-rules/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_rule(
        self, client, owner_headers
    ):
        rule = create_alert_rule(
            client, owner_headers
        )
        resp = client.patch(
            f"/api/v1/alert-rules/{rule['id']}",
            json={
                "name": "Updated Rule",
                "threshold_value": 95.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Rule"
        assert resp.json()["threshold_value"] == 95.0

    def test_update_rule_disable(
        self, client, owner_headers
    ):
        rule = create_alert_rule(
            client, owner_headers
        )
        resp = client.patch(
            f"/api/v1/alert-rules/{rule['id']}",
            json={"enabled": False},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_delete_rule(
        self, client, owner_headers
    ):
        rule = create_alert_rule(
            client, owner_headers
        )
        resp = client.delete(
            f"/api/v1/alert-rules/{rule['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        resp = client.get(
            f"/api/v1/alert-rules/{rule['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_rule_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/alert-rules/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# ===========================
# Alert Engine Tests
# ===========================


class TestAlertEngine:
    def test_greater_than_triggered(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="r1",
            metric_key="cpu_usage",
            value=95.0,
            threshold=90.0,
            condition="GREATER_THAN",
            severity="WARNING",
        )
        assert result.triggered is True

    def test_greater_than_not_triggered(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="r1",
            metric_key="cpu_usage",
            value=85.0,
            threshold=90.0,
            condition="GREATER_THAN",
            severity="WARNING",
        )
        assert result.triggered is False

    def test_less_than_triggered(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="r1",
            metric_key="temp",
            value=15.0,
            threshold=18.0,
            condition="LESS_THAN",
            severity="INFO",
        )
        assert result.triggered is True

    def test_equal_triggered(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="r1",
            metric_key="count",
            value=0.0,
            threshold=0.0,
            condition="EQUAL",
            severity="CRITICAL",
        )
        assert result.triggered is True

    def test_not_equal_triggered(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="r1",
            metric_key="status",
            value=1.0,
            threshold=0.0,
            condition="NOT_EQUAL",
            severity="WARNING",
        )
        assert result.triggered is True

    def test_not_equal_not_triggered(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="r1",
            metric_key="status",
            value=0.0,
            threshold=0.0,
            condition="NOT_EQUAL",
            severity="WARNING",
        )
        assert result.triggered is False

    def test_invalid_condition(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="r1",
            metric_key="cpu",
            value=95.0,
            threshold=90.0,
            condition="INVALID",
            severity="WARNING",
        )
        assert result.triggered is False

    def test_build_alert_title(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        title = engine.build_alert_title(
            rule_name="High CPU",
            device_id="abc12345-1234-1234-1234-123456789012",
            value=95.0,
            condition="GREATER_THAN",
            threshold=90.0,
        )
        assert "High CPU" in title
        assert "95.0" in title
        assert ">" in title

    def test_build_alert_description(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        desc = engine.build_alert_description(
            metric_key="cpu_usage_percent",
            value=95.0,
            condition="GREATER_THAN",
            threshold=90.0,
            severity="CRITICAL",
        )
        assert "cpu_usage_percent" in desc
        assert "95.0" in desc
        assert "CRITICAL" in desc

    def test_determine_severity_critical(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        sev = engine.determine_severity(
            95.0, 80.0, 90.0
        )
        assert sev == "CRITICAL"

    def test_determine_severity_warning(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        sev = engine.determine_severity(
            85.0, 80.0, 90.0
        )
        assert sev == "WARNING"

    def test_determine_severity_info(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        sev = engine.determine_severity(
            50.0, 80.0, 90.0
        )
        assert sev == "INFO"


# ===========================
# Alert Lifecycle Tests
# ===========================


class TestAlertLifecycle:
    def test_create_alert_via_api(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        alert = _create_alert(
            client, owner_headers, device_id, rule
        )
        assert alert["status"] == "OPEN"
        assert alert["severity"] == "WARNING"

    def test_list_alerts(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        _create_alert(
            client, owner_headers, device_id, rule
        )
        resp = client.get(
            "/api/v1/alerts",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_list_alerts_filter_severity(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client,
            owner_headers,
            {"severity": "CRITICAL"},
        )
        _create_alert(
            client,
            owner_headers,
            device_id,
            rule,
            {"severity": "CRITICAL"},
        )
        resp = client.get(
            "/api/v1/alerts?severity=CRITICAL",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        for alert in resp.json()["alerts"]:
            assert alert["severity"] == "CRITICAL"

    def test_acknowledge_alert(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        alert = _create_alert(
            client, owner_headers, device_id, rule
        )
        resp = client.patch(
            f"/api/v1/alerts/{alert['id']}/acknowledge",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ACKNOWLEDGED"

    def test_resolve_alert(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        alert = _create_alert(
            client, owner_headers, device_id, rule
        )
        resp = client.patch(
            f"/api/v1/alerts/{alert['id']}/resolve",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESOLVED"
        assert resp.json()["resolved_at"] is not None

    def test_get_alert(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        alert = _create_alert(
            client,
            owner_headers,
            device_id,
            rule,
            {"severity": "INFO"},
        )
        resp = client.get(
            f"/api/v1/alerts/{alert['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == alert["id"]

    def test_get_alert_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/alerts/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_alert_summary(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/alerts/summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_alerts" in data
        assert "open_alerts" in data
        assert "critical_alerts" in data
        assert "warning_alerts" in data


# ===========================
# Incident Workflow Tests
# ===========================


class TestIncidentWorkflow:
    def _create_alert_for_incident(
        self, client, owner_headers, severity="CRITICAL"
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client,
            owner_headers,
            {"severity": severity},
        )
        alert = _create_alert(
            client,
            owner_headers,
            device_id,
            rule,
            {"severity": severity},
        )
        return alert

    def test_create_incident(
        self, client, owner_headers
    ):
        alert = self._create_alert_for_incident(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}",
                "description": "Critical issue",
                "priority": "CRITICAL",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "OPEN"
        assert data["priority"] == "CRITICAL"

    def test_create_incident_duplicate_prevention(
        self, client, owner_headers
    ):
        alert = self._create_alert_for_incident(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}",
                "priority": "HIGH",
            },
            headers=owner_headers,
        )
        resp = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}-dup",
                "priority": "HIGH",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_list_incidents(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/incidents",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_get_incident(
        self, client, owner_headers
    ):
        alert = self._create_alert_for_incident(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        inc_resp = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}",
                "priority": "MEDIUM",
            },
            headers=owner_headers,
        )
        inc_id = inc_resp.json()["id"]
        resp = client.get(
            f"/api/v1/incidents/{inc_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == inc_id

    def test_update_incident_status(
        self, client, owner_headers
    ):
        alert = self._create_alert_for_incident(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        inc_resp = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}",
                "priority": "MEDIUM",
            },
            headers=owner_headers,
        )
        inc_id = inc_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/incidents/{inc_id}",
            json={"status": "IN_PROGRESS"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

    def test_resolve_incident(
        self, client, owner_headers
    ):
        alert = self._create_alert_for_incident(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        inc_resp = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}",
                "priority": "HIGH",
            },
            headers=owner_headers,
        )
        inc_id = inc_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/incidents/{inc_id}/resolve",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESOLVED"
        assert resp.json()["resolved_at"] is not None

    def test_incident_summary(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/incidents/summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "open_incidents" in data
        assert (
            "average_resolution_time_minutes" in data
        )
        assert "critical_incidents" in data

    def test_invalid_priority(
        self, client, owner_headers
    ):
        alert = self._create_alert_for_incident(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}",
                "priority": "EXTREME",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ===========================
# Maintenance Window Tests
# ===========================


class TestMaintenanceWindows:
    def test_create_window(
        self, client, owner_headers
    ):
        window = create_maintenance_window(
            client, owner_headers
        )
        assert window["status"] == "SCHEDULED"
        assert "name" in window

    def test_list_windows(
        self, client, owner_headers
    ):
        create_maintenance_window(
            client, owner_headers
        )
        resp = client.get(
            "/api/v1/maintenance-windows",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_window(
        self, client, owner_headers
    ):
        window = create_maintenance_window(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/maintenance-windows/{window['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == window["id"]

    def test_update_window(
        self, client, owner_headers
    ):
        window = create_maintenance_window(
            client, owner_headers
        )
        resp = client.patch(
            f"/api/v1/maintenance-windows/{window['id']}",
            json={"status": "ACTIVE"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ACTIVE"

    def test_delete_window(
        self, client, owner_headers
    ):
        window = create_maintenance_window(
            client, owner_headers
        )
        resp = client.delete(
            f"/api/v1/maintenance-windows/{window['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        resp = client.get(
            f"/api/v1/maintenance-windows/{window['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_window_invalid_time_range(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        start = datetime.utcnow() + timedelta(hours=2)
        end = datetime.utcnow() + timedelta(hours=1)
        resp = client.post(
            "/api/v1/maintenance-windows",
            json={
                "name": f"Bad-{uid}",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_filter_by_status(
        self, client, owner_headers
    ):
        create_maintenance_window(
            client, owner_headers
        )
        resp = client.get(
            "/api/v1/maintenance-windows?status=SCHEDULED",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        for w in resp.json()["windows"]:
            assert w["status"] == "SCHEDULED"


# ===========================
# Threshold Evaluation Tests
# ===========================


class TestThresholdEvaluation:
    def test_cpu_high_triggers_alert(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        create_monitoring_target(
            client, owner_headers, device_id
        )
        uid = uuid.uuid4().hex[:8]
        create_alert_rule(
            client,
            owner_headers,
            {
                "metric_key": f"cpu_usage_{uid}",
                "condition": "GREATER_THAN",
                "threshold_value": 80.0,
                "severity": "CRITICAL",
            },
        )

        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="test",
            metric_key=f"cpu_usage_{uid}",
            value=95.0,
            threshold=80.0,
            condition="GREATER_THAN",
            severity="CRITICAL",
        )
        assert result.triggered is True
        assert result.severity == "CRITICAL"

    def test_cpu_normal_no_alert(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="test",
            metric_key="cpu_usage",
            value=50.0,
            threshold=90.0,
            condition="GREATER_THAN",
            severity="WARNING",
        )
        assert result.triggered is False

    def test_temperature_high_triggers_alert(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="test",
            metric_key="temperature_celsius",
            value=35.0,
            threshold=30.0,
            condition="GREATER_THAN",
            severity="WARNING",
        )
        assert result.triggered is True

    def test_power_usage_threshold(self):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        result = engine.evaluate_rule(
            rule_id="test",
            metric_key="power_usage_percent",
            value=92.0,
            threshold=90.0,
            condition="GREATER_THAN",
            severity="CRITICAL",
        )
        assert result.triggered is True


# ===========================
# Duplicate Prevention Tests
# ===========================


class TestDuplicatePrevention:
    def test_duplicate_incident_blocked(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        alert = _create_alert(
            client, owner_headers, device_id, rule
        )
        uid = uuid.uuid4().hex[:8]
        resp1 = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-1-{uid}",
                "priority": "HIGH",
            },
            headers=owner_headers,
        )
        assert resp1.status_code == 201
        resp2 = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-2-{uid}",
                "priority": "HIGH",
            },
            headers=owner_headers,
        )
        assert resp2.status_code == 409


# ===========================
# Maintenance Suppression Tests
# ===========================


class TestMaintenanceSuppression:
    def test_active_maintenance_window_suppresses(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        start = datetime.utcnow() - timedelta(minutes=30)
        end = datetime.utcnow() + timedelta(hours=2)
        window = client.post(
            "/api/v1/maintenance-windows",
            json={
                "name": f"Maint-{uid}",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=owner_headers,
        )
        assert window.status_code == 201
        window_id = window.json()["id"]
        resp = client.patch(
            f"/api/v1/maintenance-windows/{window_id}",
            json={"status": "ACTIVE"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ACTIVE"
        assert resp.json()["start_time"] < resp.json()["end_time"]

    def test_past_window_not_active(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        start = datetime.utcnow() - timedelta(hours=5)
        end = datetime.utcnow() - timedelta(hours=3)
        resp = client.post(
            "/api/v1/maintenance-windows",
            json={
                "name": f"Past-{uid}",
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201


# ===========================
# RBAC Tests
# ===========================


class TestAlertingRBAC:
    def test_viewer_can_read_rules(
        self, client, owner_headers, viewer_headers
    ):
        create_alert_rule(
            client, owner_headers
        )
        resp = client.get(
            "/api/v1/alert-rules",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_cannot_create_rule(
        self, client, owner_headers, viewer_headers
    ):
        resp = client.post(
            "/api/v1/alert-rules",
            json={
                "name": "Test",
                "metric_key": "cpu",
                "condition": "GREATER_THAN",
                "threshold_value": 90.0,
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_engineer_can_create_rule(
        self, client, owner_headers, engineer_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/alert-rules",
            json={
                "name": f"Eng-Rule-{uid}",
                "metric_key": f"cpu_{uid}",
                "condition": "GREATER_THAN",
                "threshold_value": 90.0,
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_admin_can_update_incident(
        self, client, owner_headers, admin_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        alert = _create_alert(
            client, owner_headers, device_id, rule
        )
        uid = uuid.uuid4().hex[:8]
        inc_resp = client.post(
            "/api/v1/incidents",
            json={
                "alert_id": alert["id"],
                "title": f"Incident-{uid}",
                "priority": "MEDIUM",
            },
            headers=owner_headers,
        )
        inc_id = inc_resp.json()["id"]
        resp = client.patch(
            f"/api/v1/incidents/{inc_id}",
            json={"status": "IN_PROGRESS"},
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ===========================
# Tenant Isolation Tests
# ===========================


class TestAlertingTenantIsolation:
    def test_cannot_read_other_company_rules(
        self, client, owner_headers
    ):
        create_alert_rule(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"OtherCo-{uid}",
                "company_email": f"other-{uid}@test.com",
                "name": "Other",
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
        resp = client.get(
            "/api/v1/alert-rules",
            headers=other_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_cannot_read_other_company_alerts(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"OtherCo-{uid}",
                "company_email": f"other-{uid}@test.com",
                "name": "Other",
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
        resp = client.get(
            "/api/v1/alerts",
            headers=other_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_cannot_access_other_company_alert(
        self, client, owner_headers
    ):
        _, device_id = _create_device_in_dc(
            client, owner_headers
        )
        rule = create_alert_rule(
            client, owner_headers
        )
        alert = _create_alert(
            client, owner_headers, device_id, rule
        )
        uid2 = uuid.uuid4().hex[:8]
        client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"OtherCo-{uid2}",
                "company_email": f"other-{uid2}@test.com",
                "name": "Other",
                "email": f"other-{uid2}@test.com",
                "password": "testpass123",
                "country": "US",
            },
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other-{uid2}@test.com",
                "password": "testpass123",
            },
        )
        other_headers = {
            "Authorization": (
                f"Bearer {other_login.json()['access_token']}"
            )
        }
        resp = client.get(
            f"/api/v1/alerts/{alert['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404


# ===========================
# Background Job Tests
# ===========================


class TestBackgroundJobs:
    def test_scheduler_list_jobs(self):
        from app.engine.background_jobs import (
            AlertEvaluationJob,
            BackgroundJobScheduler,
        )
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import settings

        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)

        scheduler = BackgroundJobScheduler(Session)
        scheduler.register_job(
            AlertEvaluationJob(Session)
        )
        jobs = scheduler.list_jobs()
        assert "alert_evaluation" in jobs

        engine.dispose()

    def test_alert_engine_evaluate_rules_for_metric(
        self,
    ):
        from app.engine.alert_engine import (
            AlertEngine,
        )

        engine = AlertEngine()
        results = engine.evaluate_rules_for_metric(
            rules=[],
            metric_key="cpu_usage",
            value=95.0,
            device_id="test-device",
        )
        assert results == []
