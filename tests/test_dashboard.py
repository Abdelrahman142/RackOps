import uuid

import pytest

from tests.conftest import (
    create_alert_rule,
    create_building,
    create_cooling_unit,
    create_device,
    create_floor,
    create_interface,
    create_ip,
    create_maintenance_window,
    create_pdu,
    create_room,
    create_sensor,
    create_subnet,
    create_ups,
    create_vlan,
    create_zone,
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
    building = create_building(client, headers, dc_id)
    building_id = building["id"]
    floor = create_floor(client, headers, building_id)
    floor_id = floor["id"]
    room = create_room(client, headers, floor_id)
    room_id = room["id"]
    return dc_id, building_id, floor_id, room_id


def _create_rack_with_device(client, headers, room_id):
    uid = uuid.uuid4().hex[:8]
    rack = client.post(
        f"/api/v1/rooms/{room_id}/racks",
        json={
            "name": f"Rack-{uid}",
            "code": f"RK{uid[:4].upper()}",
            "rack_type": "SERVER_RACK",
            "status": "ACTIVE",
            "height_units": 42,
            "power_capacity_kw": 10.0,
            "current_power_usage_kw": 3.0,
            "max_weight_kg": 800.0,
            "current_weight_kg": 200.0,
            "cooling_capacity_kw": 8.0,
        },
        headers=headers,
    ).json()
    device = create_device(client, headers, rack["id"])
    return rack, device


# ===========================
# Dashboard Overview
# ===========================


class TestDashboardOverview:
    def test_overview_empty_company(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/overview",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "entity_counts" in data
        assert "health_summary" in data
        assert "power_summary" in data
        assert "alert_summary" in data
        assert data["entity_counts"]["datacenters"] == 0

    def test_overview_counts_entities(
        self, client, owner_headers
    ):
        dc_id, building_id, floor_id, room_id = (
            _create_full_dc_stack(client, owner_headers)
        )
        rack, device = _create_rack_with_device(
            client, owner_headers, room_id
        )
        create_ups(client, owner_headers, room_id)
        create_pdu(client, owner_headers, room_id)
        create_cooling_unit(client, owner_headers, room_id)
        zone = create_zone(client, owner_headers, room_id)
        create_sensor(client, owner_headers, zone["id"])

        resp = client.get(
            "/api/v1/dashboard/overview",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        counts = resp.json()["entity_counts"]
        assert counts["datacenters"] == 1
        assert counts["buildings"] == 1
        assert counts["floors"] == 1
        assert counts["rooms"] == 1
        assert counts["racks"] == 1
        assert counts["devices"] == 1
        assert counts["ups_systems"] == 1
        assert counts["pdus"] == 1
        assert counts["cooling_units"] == 1
        assert counts["sensors"] == 1

    def test_overview_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard/overview")
        assert resp.status_code in (401, 403)

    def test_overview_requires_viewer_role(
        self, client, viewer_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/overview",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_overview_includes_health_summary(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/overview",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        hs = resp.json()["health_summary"]
        assert hs["total_checks"] == 0
        assert hs["healthy"] == 0
        assert hs["warning"] == 0
        assert hs["critical"] == 0

    def test_overview_includes_alert_summary(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/overview",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        al = resp.json()["alert_summary"]
        assert al["active_alerts"] == 0
        assert al["critical_alerts"] == 0
        assert al["open_incidents"] == 0

    def test_overview_power_summary_empty(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/overview",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        ps = resp.json()["power_summary"]
        assert ps["total_capacity_kw"] == 0.0
        assert ps["total_actual_kw"] == 0.0

    def test_overview_isolation_between_companies(
        self, client, admin_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, admin_headers
        )
        _create_rack_with_device(client, admin_headers, room_id)

        resp = client.get(
            "/api/v1/dashboard/overview",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["entity_counts"]["racks"] == 1

        uid = uuid.uuid4().hex[:8]
        client.post(
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
        other_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other-{uid}@test.com",
                "password": "testpass123",
            },
        )
        other_headers = {
            "Authorization": f"Bearer {other_resp.json()['access_token']}"
        }
        resp2 = client.get(
            "/api/v1/dashboard/overview",
            headers=other_headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["entity_counts"]["racks"] == 0
        assert resp2.status_code == 200
        assert resp2.json()["entity_counts"]["racks"] == 0


# ===========================
# Power Dashboard
# ===========================


class TestPowerDashboard:
    def test_power_dashboard_empty(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ups_count"] == 0
        assert data["pdu_count"] == 0
        assert data["total_ups_capacity_kva"] == 0.0
        assert data["rack_power_details"] == []

    def test_power_dashboard_with_infrastructure(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        create_ups(
            client, owner_headers, room_id,
            overrides={"capacity_kva": 10.0},
        )
        create_ups(
            client, owner_headers, room_id,
            overrides={"capacity_kva": 5.0},
        )
        create_pdu(client, owner_headers, room_id)

        uid = uuid.uuid4().hex[:8]
        rack = client.post(
            f"/api/v1/rooms/{room_id}/racks",
            json={
                "name": f"Rack-{uid}",
                "code": f"RK{uid[:4].upper()}",
                "rack_type": "SERVER_RACK",
                "status": "ACTIVE",
                "height_units": 42,
                "power_capacity_kw": 20.0,
                "current_power_usage_kw": 12.0,
                "max_weight_kg": 800.0,
                "current_weight_kg": 200.0,
            },
            headers=owner_headers,
        ).json()

        resp = client.get(
            "/api/v1/dashboard/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ups_count"] == 2
        assert data["pdu_count"] == 1
        assert data["total_ups_capacity_kva"] == 15.0
        assert data["total_rack_power_capacity_kw"] == 20.0
        assert data["total_rack_power_usage_kw"] == 12.0
        assert data["rack_utilization_percent"] == 60.0
        assert len(data["rack_power_details"]) == 1

    def test_power_dashboard_rack_power_detail_fields(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        rack = client.post(
            f"/api/v1/rooms/{room_id}/racks",
            json={
                "name": f"Rack-{uid}",
                "code": f"RK{uid[:4].upper()}",
                "rack_type": "SERVER_RACK",
                "status": "ACTIVE",
                "height_units": 42,
                "power_capacity_kw": 15.0,
                "current_power_usage_kw": 8.0,
                "max_weight_kg": 500.0,
                "current_weight_kg": 100.0,
            },
            headers=owner_headers,
        ).json()

        resp = client.get(
            "/api/v1/dashboard/power",
            headers=owner_headers,
        )
        detail = resp.json()["rack_power_details"][0]
        assert detail["rack_id"] == rack["id"]
        assert detail["rack_name"] == rack["name"]
        assert detail["rack_code"] == rack["code"]
        assert detail["room_name"] is not None

    def test_power_dashboard_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard/power")
        assert resp.status_code in (401, 403)

    def test_power_dashboard_isolation(
        self, client, admin_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, admin_headers
        )
        create_ups(
            client, admin_headers, room_id,
            overrides={"capacity_kva": 20.0},
        )

        resp = client.get(
            "/api/v1/dashboard/power",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["ups_count"] == 1

        uid = uuid.uuid4().hex[:8]
        client.post(
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
        other_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other-{uid}@test.com",
                "password": "testpass123",
            },
        )
        other_headers = {
            "Authorization": f"Bearer {other_resp.json()['access_token']}"
        }
        resp2 = client.get(
            "/api/v1/dashboard/power",
            headers=other_headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["ups_count"] == 0
        assert resp2.status_code == 200
        assert resp2.json()["ups_count"] == 0


# ===========================
# Cooling Dashboard
# ===========================


class TestCoolingDashboard:
    def test_cooling_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/dashboard/cooling",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cooling_units"] == 0
        assert data["active_units"] == 0
        assert data["zone_count"] == 0
        assert data["sensor_count"] == 0

    def test_cooling_with_infrastructure(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        create_cooling_unit(client, owner_headers, room_id)
        create_cooling_unit(
            client, owner_headers, room_id,
            overrides={"status": "OFFLINE"},
        )
        zone = create_zone(client, owner_headers, room_id)
        create_sensor(client, owner_headers, zone["id"])
        create_sensor(
            client, owner_headers, zone["id"],
            overrides={"sensor_type": "HUMIDITY"},
        )

        resp = client.get(
            "/api/v1/dashboard/cooling",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cooling_units"] == 2
        assert data["active_units"] == 1
        assert data["inactive_units"] == 1
        assert data["zone_count"] == 1
        assert data["sensor_count"] == 2

    def test_cooling_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard/cooling")
        assert resp.status_code in (401, 403)


# ===========================
# Network Dashboard
# ===========================


class TestNetworkDashboard:
    def test_network_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/dashboard/network",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_interfaces"] == 0
        assert data["total_connections"] == 0
        assert data["total_vlans"] == 0
        assert data["total_subnets"] == 0
        assert data["total_ip_addresses"] == 0

    def test_network_with_infrastructure(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        rack, device = _create_rack_with_device(
            client, owner_headers, room_id
        )
        iface1 = create_interface(
            client, owner_headers, device["id"]
        )
        iface2 = create_interface(
            client, owner_headers, device["id"],
            overrides={"name": "eth1", "status": "DOWN"},
        )
        create_vlan(client, owner_headers, dc_id)
        vlan = create_vlan(
            client, owner_headers, dc_id,
            overrides={"name": "VLAN-200", "vlan_id": 200},
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        create_ip(client, owner_headers, subnet["id"])

        resp = client.get(
            "/api/v1/dashboard/network",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_interfaces"] == 2
        assert data["interfaces_up"] == 1
        assert data["interfaces_down"] == 1
        assert data["total_vlans"] == 2
        assert data["total_subnets"] == 1
        assert data["total_ip_addresses"] == 1

    def test_network_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard/network")
        assert resp.status_code in (401, 403)


# ===========================
# Capacity Overview
# ===========================


class TestCapacityOverview:
    def test_capacity_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/dashboard/capacity",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["rack_space_used_units"] == 0
        assert data["rack_space_total_units"] == 0

    def test_capacity_with_racks_and_devices(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        rack = client.post(
            f"/api/v1/rooms/{room_id}/racks",
            json={
                "name": f"Rack-{uid}",
                "code": f"RK{uid[:4].upper()}",
                "rack_type": "SERVER_RACK",
                "status": "ACTIVE",
                "height_units": 42,
                "power_capacity_kw": 10.0,
                "current_power_usage_kw": 4.0,
                "max_weight_kg": 500.0,
                "current_weight_kg": 150.0,
                "cooling_capacity_kw": 8.0,
            },
            headers=owner_headers,
        ).json()
        create_device(
            client, owner_headers,
            rack["id"],
            overrides={"rack_unit_height": 2},
        )

        resp = client.get(
            "/api/v1/dashboard/capacity",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_rack_power_capacity_kw"] == 10.0
        assert data["total_rack_power_usage_kw"] == 4.0
        assert data["power_utilization_percent"] == 40.0
        assert data["total_weight_capacity_kg"] == 500.0
        assert data["total_weight_current_kg"] == 150.0
        assert data["weight_utilization_percent"] == 30.0
        assert data["rack_space_total_units"] == 42
        assert data["rack_space_used_units"] == 2

    def test_capacity_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard/capacity")
        assert resp.status_code in (401, 403)


# ===========================
# Capacity Forecast
# ===========================


class TestCapacityForecast:
    def test_forecast_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/dashboard/capacity/forecast",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["days_ahead"] == 30
        assert data["projected_power_capacity_kw"] == 0.0

    def test_forecast_with_custom_days(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/capacity/forecast?days_ahead=60",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["days_ahead"] == 60

    def test_forecast_validation_too_many_days(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/capacity/forecast?days_ahead=500",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_forecast_requires_auth(self, client):
        resp = client.get(
            "/api/v1/dashboard/capacity/forecast"
        )
        assert resp.status_code in (401, 403)


# ===========================
# Power Trends
# ===========================


class TestPowerTrends:
    def test_trends_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/dashboard/power/trends",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_trends_with_custom_days(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/power/trends?days=14",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_trends_validation_too_many_days(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/dashboard/power/trends?days=100",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_trends_requires_auth(self, client):
        resp = client.get("/api/v1/dashboard/power/trends")
        assert resp.status_code in (401, 403)


# ===========================
# RBAC
# ===========================


class TestDashboardRBAC:
    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/dashboard/overview",
            "/api/v1/dashboard/power",
            "/api/v1/dashboard/cooling",
            "/api/v1/dashboard/network",
            "/api/v1/dashboard/capacity",
            "/api/v1/dashboard/capacity/forecast",
            "/api/v1/dashboard/power/trends",
        ],
    )
    def test_all_endpoints_accept_viewer(
        self, client, viewer_headers, endpoint
    ):
        resp = client.get(endpoint, headers=viewer_headers)
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/dashboard/overview",
            "/api/v1/dashboard/power",
            "/api/v1/dashboard/cooling",
            "/api/v1/dashboard/network",
            "/api/v1/dashboard/capacity",
            "/api/v1/dashboard/capacity/forecast",
            "/api/v1/dashboard/power/trends",
        ],
    )
    def test_all_endpoints_accept_admin(
        self, client, admin_headers, endpoint
    ):
        resp = client.get(endpoint, headers=admin_headers)
        assert resp.status_code == 200
