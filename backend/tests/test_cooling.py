import uuid

import pytest


def create_room_chain(client, owner_headers):
    uid = uuid.uuid4().hex[:8]
    resp = client.post(
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
        headers=owner_headers,
    )
    dc_id = resp.json()["id"]

    resp = client.post(
        f"/api/v1/datacenters/{dc_id}/buildings",
        json={
            "name": f"Bld-{uid}",
            "code": f"BL{uid[:4].upper()}",
            "address": "123 Main St",
            "status": "ACTIVE",
            "number_of_floors": 1,
        },
        headers=owner_headers,
    )
    bld_id = resp.json()["id"]

    resp = client.post(
        f"/api/v1/buildings/{bld_id}/floors",
        json={
            "name": f"Flr-{uid}",
            "code": f"FL{uid[:4].upper()}",
            "floor_number": 1,
            "status": "ACTIVE",
        },
        headers=owner_headers,
    )
    floor_id = resp.json()["id"]

    resp = client.post(
        f"/api/v1/floors/{floor_id}/rooms",
        json={
            "name": f"Room-{uid}",
            "code": f"RM{uid[:4].upper()}",
            "room_type": "SERVER_ROOM",
            "status": "ACTIVE",
            "max_rack_capacity": 10,
        },
        headers=owner_headers,
    )
    room_id = resp.json()["id"]

    return dc_id, room_id


# =====================================================
# Cooling Unit CRUD Tests
# =====================================================


class TestCreateCoolingUnit:
    def test_create_crac_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-01",
                "manufacturer": "Liebert",
                "model": "DFS",
                "serial_number": "CRAC-SN-001",
                "type": "CRAC",
                "status": "ACTIVE",
                "cooling_capacity_kw": 10.0,
                "airflow_cfm": 2000.0,
                "power_consumption_kw": 3.5,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "CRAC-01"
        assert data["type"] == "CRAC"
        assert data["cooling_capacity_kw"] == 10.0
        assert data["airflow_cfm"] == 2000.0
        assert data["serial_number"] == "CRAC-SN-001"

    def test_create_chiller_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CHILLER-01",
                "type": "CHILLER",
                "cooling_capacity_kw": 50.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["type"] == "CHILLER"

    def test_create_crah_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAH-01",
                "type": "CRAH",
                "cooling_capacity_kw": 15.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["type"] == "CRAH"

    def test_create_fan_wall_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "FW-01",
                "type": "FAN_WALL",
                "cooling_capacity_kw": 20.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["type"] == "FAN_WALL"

    def test_create_unit_minimal(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-Min",
                "cooling_capacity_kw": 5.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "CRAC"
        assert data["status"] == "ACTIVE"

    def test_create_unit_duplicate_name_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-Dup",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-Dup",
                "cooling_capacity_kw": 15.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_unit_duplicate_serial_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-01",
                "cooling_capacity_kw": 10.0,
                "serial_number": "SN-DUP",
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-02",
                "cooling_capacity_kw": 15.0,
                "serial_number": "SN-DUP",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_unit_room_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/rooms/{fake_id}/cooling-units",
            json={
                "name": "CRAC-01",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_unit_invalid_type_422(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-01",
                "cooling_capacity_kw": 10.0,
                "type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_unit_invalid_status_422(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-01",
                "cooling_capacity_kw": 10.0,
                "status": "BOGUS",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_unit_capacity_zero_422(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-01",
                "cooling_capacity_kw": 0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


class TestGetCoolingUnit:
    def test_get_unit_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-Get",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        unit_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/cooling-units/{unit_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "CRAC-Get"

    def test_get_unit_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/cooling-units/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestListCoolingUnits:
    def test_list_units_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-A",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-B",
                "cooling_capacity_kw": 15.0,
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/cooling-units",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["cooling_units"]) == 2

    def test_list_units_empty_room(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/rooms/{room_id}/cooling-units",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestUpdateCoolingUnit:
    def test_update_unit_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-Old",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        unit_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/cooling-units/{unit_id}",
            json={
                "name": "CRAC-New",
                "cooling_capacity_kw": 15.0,
                "status": "MAINTENANCE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "CRAC-New"
        assert data["cooling_capacity_kw"] == 15.0
        assert data["status"] == "MAINTENANCE"

    def test_update_unit_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/cooling-units/{fake_id}",
            json={"name": "X"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_unit_duplicate_name_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-A",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-B",
                "cooling_capacity_kw": 15.0,
            },
            headers=owner_headers,
        )
        unit_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/cooling-units/{unit_id}",
            json={"name": "CRAC-A"},
            headers=owner_headers,
        )
        assert resp.status_code == 409


class TestDeleteCoolingUnit:
    def test_delete_unit_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-Del",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        unit_id = create_resp.json()["id"]

        resp = client.delete(
            f"/api/v1/cooling-units/{unit_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/api/v1/cooling-units/{unit_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_unit_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/cooling-units/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# =====================================================
# Zone CRUD Tests
# =====================================================


class TestCreateZone:
    def test_create_zone_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={
                "name": "Zone-A",
                "description": "Server zone",
                "target_temperature_min": 18.0,
                "target_temperature_max": 27.0,
                "target_humidity_min": 30.0,
                "target_humidity_max": 60.0,
                "status": "ACTIVE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Zone-A"
        assert data["target_temperature_min"] == 18.0
        assert data["target_temperature_max"] == 27.0
        assert data["target_humidity_min"] == 30.0
        assert data["target_humidity_max"] == 60.0

    def test_create_zone_minimal(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={
                "name": "Zone-Min",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["target_temperature_min"] is None

    def test_create_zone_duplicate_name_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-Dup"},
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-Dup"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_zone_temp_range_invalid(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={
                "name": "Zone-Bad",
                "target_temperature_min": 30.0,
                "target_temperature_max": 20.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_zone_humidity_range_invalid(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={
                "name": "Zone-Bad",
                "target_humidity_min": 70.0,
                "target_humidity_max": 40.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


class TestGetZone:
    def test_get_zone_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-Get"},
            headers=owner_headers,
        )
        zone_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/zones/{zone_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Zone-Get"

    def test_get_zone_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/zones/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestListZones:
    def test_list_zones_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-A"},
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-B"},
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/zones",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_zones_empty(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/rooms/{room_id}/zones",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestUpdateZone:
    def test_update_zone_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={
                "name": "Zone-Old",
                "target_temperature_min": 18.0,
            },
            headers=owner_headers,
        )
        zone_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/zones/{zone_id}",
            json={
                "name": "Zone-New",
                "target_temperature_min": 20.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Zone-New"
        assert data["target_temperature_min"] == 20.0

    def test_update_zone_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/zones/{fake_id}",
            json={"name": "X"},
            headers=owner_headers,
        )
        assert resp.status_code == 404


# =====================================================
# Sensor CRUD Tests
# =====================================================


class TestCreateSensor:
    def test_create_temp_sensor(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-S1"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Temp-01",
                "sensor_type": "TEMPERATURE",
                "location_description": "Rack Row A",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Temp-01"
        assert data["sensor_type"] == "TEMPERATURE"
        assert data["last_value"] is None

    def test_create_humidity_sensor(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-S2"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Hum-01",
                "sensor_type": "HUMIDITY",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["sensor_type"] == "HUMIDITY"

    def test_create_smoke_sensor(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-S3"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Smoke-01",
                "sensor_type": "SMOKE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["sensor_type"] == "SMOKE"

    def test_create_water_leak_sensor(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-S4"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Leak-01",
                "sensor_type": "WATER_LEAK",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201

    def test_create_sensor_duplicate_name_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-Dup"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Sensor-Dup",
                "sensor_type": "TEMPERATURE",
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Sensor-Dup",
                "sensor_type": "HUMIDITY",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_sensor_zone_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/zones/{fake_id}/sensors",
            json={
                "name": "Sensor-01",
                "sensor_type": "TEMPERATURE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_sensor_invalid_type_422(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-Bad"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Sensor-Bad",
                "sensor_type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


class TestGetSensor:
    def test_get_sensor_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-G"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        sensor_resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Temp-Get",
                "sensor_type": "TEMPERATURE",
            },
            headers=owner_headers,
        )
        sensor_id = sensor_resp.json()["id"]

        resp = client.get(
            f"/api/v1/sensors/{sensor_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Temp-Get"

    def test_get_sensor_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/sensors/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestListSensors:
    def test_list_sensors_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-L"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Temp-01",
                "sensor_type": "TEMPERATURE",
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Hum-01",
                "sensor_type": "HUMIDITY",
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/zones/{zone_id}/sensors",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_sensors_empty_zone(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-Empty"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        resp = client.get(
            f"/api/v1/zones/{zone_id}/sensors",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# =====================================================
# Environmental Summary Tests
# =====================================================


class TestRoomEnvironmentSummary:
    def test_summary_empty_room(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/environment-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["room_id"] == room_id
        assert data["current_temperature"] is None
        assert data["current_humidity"] is None
        assert data["total_cooling_units"] == 0
        assert data["environmental_health"] == "NORMAL"

    def test_summary_with_cooling(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-S",
                "cooling_capacity_kw": 10.0,
                "status": "ACTIVE",
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/environment-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_cooling_units"] == 1
        assert data["cooling_capacity_kw"] == 10.0

    def test_summary_with_zone_and_sensors(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )

        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={
                "name": "Zone-Sum",
                "target_temperature_min": 18.0,
                "target_temperature_max": 27.0,
            },
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        temp_resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Temp-Sum",
                "sensor_type": "TEMPERATURE",
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/environment-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["zones"]) == 1
        assert data["zones"][0]["zone_name"] == "Zone-Sum"

    def test_summary_room_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/rooms/{fake_id}/environment-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestDataCenterEnvironmentSummary:
    def test_dc_summary_empty(
        self, client, owner_headers
    ):
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
            headers=owner_headers,
        )
        dc_id = dc_resp.json()["id"]

        resp = client.get(
            f"/api/v1/datacenters/{dc_id}/environment-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["datacenter_id"] == dc_id
        assert data["total_cooling_units"] == 0
        assert data["room_count"] == 0

    def test_dc_summary_with_cooling(
        self, client, owner_headers
    ):
        dc_id, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-DC",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/datacenters/{dc_id}/environment-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cooling_units"] == 1
        assert data["total_cooling_capacity_kw"] == 10.0

    def test_dc_summary_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/datacenters/{fake_id}/environment-summary",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# =====================================================
# RBAC Tests
# =====================================================


class TestCoolingRBAC:
    def test_viewer_cannot_create_cooling_unit(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-V",
                "cooling_capacity_kw": 10.0,
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_zone(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-V"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_sensor(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-SV"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Sensor-V",
                "sensor_type": "TEMPERATURE",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_can_read_cooling_unit(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-R",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        unit_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/cooling-units/{unit_id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_can_read_zone(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-R"},
            headers=owner_headers,
        )
        zone_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/zones/{zone_id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_can_read_sensor(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        zone_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-SR"},
            headers=owner_headers,
        )
        zone_id = zone_resp.json()["id"]

        sensor_resp = client.post(
            f"/api/v1/zones/{zone_id}/sensors",
            json={
                "name": "Temp-R",
                "sensor_type": "TEMPERATURE",
            },
            headers=owner_headers,
        )
        sensor_id = sensor_resp.json()["id"]

        resp = client.get(
            f"/api/v1/sensors/{sensor_id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_admin_can_create_cooling_unit(
        self, client, owner_headers, admin_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-A",
                "cooling_capacity_kw": 10.0,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_engineer_can_create_zone(
        self, client, owner_headers, engineer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-E"},
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_viewer_can_read_environment_summary(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/rooms/{room_id}/environment-summary",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_unauthenticated_returns_401(
        self, client
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/rooms/{fake_id}/cooling-units",
        )
        assert resp.status_code == 401


# =====================================================
# Soft Delete Tests
# =====================================================


class TestSoftDelete:
    def test_deleted_cooling_unit_hidden(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/cooling-units",
            json={
                "name": "CRAC-SD",
                "cooling_capacity_kw": 10.0,
            },
            headers=owner_headers,
        )
        unit_id = create_resp.json()["id"]

        client.delete(
            f"/api/v1/cooling-units/{unit_id}",
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/cooling-units",
            headers=owner_headers,
        )
        assert resp.json()["total"] == 0

    def test_deleted_zone_hidden(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/zones",
            json={"name": "Zone-SD"},
            headers=owner_headers,
        )
        zone_id = create_resp.json()["id"]

        client.patch(
            f"/api/v1/zones/{zone_id}",
            json={"status": "OFFLINE"},
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/zones",
            headers=owner_headers,
        )
        assert resp.json()["total"] == 1
