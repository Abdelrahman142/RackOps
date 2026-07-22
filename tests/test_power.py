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


def create_rack_in_room(client, owner_headers, room_id):
    uid = uuid.uuid4().hex[:8]
    resp = client.post(
        f"/api/v1/rooms/{room_id}/racks",
        json={
            "name": f"Rack-{uid}",
            "code": f"RK{uid[:4].upper()}",
            "rack_type": "SERVER_RACK",
            "status": "ACTIVE",
            "height_units": 42,
            "power_capacity_kw": 10.0,
        },
        headers=owner_headers,
    )
    return resp.json()["id"]


# =====================================================
# UPS CRUD Tests
# =====================================================


class TestCreateUPS:
    def test_create_ups_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-01",
                "capacity_kva": 3.0,
                "manufacturer": "APC",
                "model": "Smart-UPS 3000",
                "serial_number": "UPS-SN-001",
                "status": "ACTIVE",
                "battery_capacity_minutes": 15,
                "input_voltage": 208.0,
                "output_voltage": 208.0,
                "efficiency_percent": 95.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "UPS-01"
        assert data["capacity_kva"] == 3.0
        assert data["manufacturer"] == "APC"
        assert data["serial_number"] == "UPS-SN-001"
        assert data["battery_capacity_minutes"] == 15
        assert data["efficiency_percent"] == 95.0
        assert "id" in data

    def test_create_ups_minimal(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-Min",
                "capacity_kva": 1.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "UPS-Min"
        assert data["status"] == "ACTIVE"
        assert data["manufacturer"] is None

    def test_create_ups_duplicate_name_returns_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-Dup",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-Dup",
                "capacity_kva": 5.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_ups_duplicate_serial_returns_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-01",
                "capacity_kva": 3.0,
                "serial_number": "SN-DUP-001",
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-02",
                "capacity_kva": 5.0,
                "serial_number": "SN-DUP-001",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_ups_room_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/rooms/{fake_id}/ups",
            json={
                "name": "UPS-01",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_ups_invalid_status_returns_422(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-01",
                "capacity_kva": 3.0,
                "status": "BOGUS",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_ups_capacity_zero_returns_422(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-01",
                "capacity_kva": 0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


class TestGetUPS:
    def test_get_ups_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-Get",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/ups/{ups_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "UPS-Get"

    def test_get_ups_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/ups/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestListUPS:
    def test_list_ups_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-A",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-B",
                "capacity_kva": 5.0,
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/ups",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["ups_systems"]) == 2

    def test_list_ups_empty_room(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/rooms/{room_id}/ups",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestUpdateUPS:
    def test_update_ups_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-Old",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/ups/{ups_id}",
            json={
                "name": "UPS-New",
                "capacity_kva": 5.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "UPS-New"
        assert resp.json()["capacity_kva"] == 5.0

    def test_update_ups_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/ups/{fake_id}",
            json={"name": "X"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_ups_duplicate_name_returns_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-A",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-B",
                "capacity_kva": 5.0,
            },
            headers=owner_headers,
        )
        ups_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/ups/{ups_id}",
            json={"name": "UPS-A"},
            headers=owner_headers,
        )
        assert resp.status_code == 409


class TestDeleteUPS:
    def test_delete_ups_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-Del",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = create_resp.json()["id"]

        resp = client.delete(
            f"/api/v1/ups/{ups_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/api/v1/ups/{ups_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_ups_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/ups/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# =====================================================
# PDU CRUD Tests
# =====================================================


class TestCreatePDU:
    def test_create_pdu_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-01",
                "total_capacity_amp": 30.0,
                "manufacturer": "APC",
                "model": "Metered PDU",
                "serial_number": "PDU-SN-001",
                "status": "ACTIVE",
                "current_usage_amp": 5.0,
                "phase_type": "SINGLE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "PDU-01"
        assert data["total_capacity_amp"] == 30.0
        assert data["current_usage_amp"] == 5.0
        assert data["phase_type"] == "SINGLE"

    def test_create_pdu_with_rack(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        rack_id = create_rack_in_room(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-Rack",
                "total_capacity_amp": 30.0,
                "rack_id": rack_id,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["rack_id"] == rack_id

    def test_create_pdu_duplicate_name_returns_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-Dup",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-Dup",
                "total_capacity_amp": 50.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_pdu_invalid_phase_type_returns_422(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-01",
                "total_capacity_amp": 30.0,
                "phase_type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_pdu_room_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/rooms/{fake_id}/pdus",
            json={
                "name": "PDU-01",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestGetPDU:
    def test_get_pdu_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-Get",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/pdus/{pdu_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "PDU-Get"

    def test_get_pdu_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/pdus/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestListPDUs:
    def test_list_pdus_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-A",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-B",
                "total_capacity_amp": 50.0,
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/pdus",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_pdus_empty_room(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/rooms/{room_id}/pdus",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestUpdatePDU:
    def test_update_pdu_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-Old",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/pdus/{pdu_id}",
            json={
                "name": "PDU-New",
                "total_capacity_amp": 50.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "PDU-New"
        assert resp.json()["total_capacity_amp"] == 50.0

    def test_update_pdu_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/pdus/{fake_id}",
            json={"name": "X"},
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestDeletePDU:
    def test_delete_pdu_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-Del",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = create_resp.json()["id"]

        resp = client.delete(
            f"/api/v1/pdus/{pdu_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/api/v1/pdus/{pdu_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_pdu_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/pdus/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# =====================================================
# PowerFeed Tests
# =====================================================


class TestCreatePowerFeed:
    def test_create_feed_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        ups_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-FEED",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = ups_resp.json()["id"]

        pdu_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-FEED",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = pdu_resp.json()["id"]

        resp = client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "UPS",
                "source_id": ups_id,
                "destination_type": "PDU",
                "destination_id": pdu_id,
                "voltage": 208.0,
                "amp_rating": 30.0,
                "status": "ACTIVE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "UPS"
        assert data["destination_type"] == "PDU"
        assert data["voltage"] == 208.0
        assert data["amp_rating"] == 30.0

    def test_create_feed_duplicate_returns_409(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        ups_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-DUP",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = ups_resp.json()["id"]

        pdu_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-DUP",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = pdu_resp.json()["id"]

        feed_data = {
            "source_type": "UPS",
            "source_id": ups_id,
            "destination_type": "PDU",
            "destination_id": pdu_id,
            "voltage": 208.0,
            "amp_rating": 30.0,
        }

        client.post(
            "/api/v1/power-feeds",
            json=feed_data,
            headers=owner_headers,
        )
        resp = client.post(
            "/api/v1/power-feeds",
            json=feed_data,
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_feed_ups_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "UPS",
                "source_id": fake_id,
                "destination_type": "PDU",
                "destination_id": fake_id,
                "voltage": 208.0,
                "amp_rating": 30.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_feed_invalid_source_type(
        self, client, owner_headers
    ):
        resp = client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "SOLAR",
                "source_id": str(uuid.uuid4()),
                "destination_type": "PDU",
                "destination_id": str(uuid.uuid4()),
                "voltage": 208.0,
                "amp_rating": 30.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


class TestGetPowerFeed:
    def test_get_feed_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        ups_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-GF",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = ups_resp.json()["id"]

        pdu_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-GF",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = pdu_resp.json()["id"]

        feed_resp = client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "UPS",
                "source_id": ups_id,
                "destination_type": "PDU",
                "destination_id": pdu_id,
                "voltage": 208.0,
                "amp_rating": 30.0,
            },
            headers=owner_headers,
        )
        feed_id = feed_resp.json()["id"]

        resp = client.get(
            f"/api/v1/power-feeds/{feed_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == feed_id

    def test_get_feed_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/power-feeds/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestListPowerFeeds:
    def test_list_feeds_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        ups_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-LF",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = ups_resp.json()["id"]

        pdu_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-LF1",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu1_id = pdu_resp.json()["id"]

        pdu_resp2 = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-LF2",
                "total_capacity_amp": 50.0,
            },
            headers=owner_headers,
        )
        pdu2_id = pdu_resp2.json()["id"]

        client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "UPS",
                "source_id": ups_id,
                "destination_type": "PDU",
                "destination_id": pdu1_id,
                "voltage": 208.0,
                "amp_rating": 30.0,
            },
            headers=owner_headers,
        )
        client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "UPS",
                "source_id": ups_id,
                "destination_type": "PDU",
                "destination_id": pdu2_id,
                "voltage": 208.0,
                "amp_rating": 50.0,
            },
            headers=owner_headers,
        )

        resp = client.get(
            "/api/v1/power-feeds",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2


class TestUpdatePowerFeed:
    def test_update_feed_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        ups_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-UF",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = ups_resp.json()["id"]

        pdu_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-UF",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = pdu_resp.json()["id"]

        feed_resp = client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "UPS",
                "source_id": ups_id,
                "destination_type": "PDU",
                "destination_id": pdu_id,
                "voltage": 208.0,
                "amp_rating": 30.0,
            },
            headers=owner_headers,
        )
        feed_id = feed_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/power-feeds/{feed_id}",
            json={"voltage": 480.0, "amp_rating": 50.0},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["voltage"] == 480.0
        assert resp.json()["amp_rating"] == 50.0


class TestDeletePowerFeed:
    def test_delete_feed_success(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        ups_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-DF",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = ups_resp.json()["id"]

        pdu_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-DF",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = pdu_resp.json()["id"]

        feed_resp = client.post(
            "/api/v1/power-feeds",
            json={
                "source_type": "UPS",
                "source_id": ups_id,
                "destination_type": "PDU",
                "destination_id": pdu_id,
                "voltage": 208.0,
                "amp_rating": 30.0,
            },
            headers=owner_headers,
        )
        feed_id = feed_resp.json()["id"]

        resp = client.delete(
            f"/api/v1/power-feeds/{feed_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/api/v1/power-feeds/{feed_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# =====================================================
# Power Summary Tests
# =====================================================


class TestRackPower:
    def test_rack_power_empty(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        rack_id = create_rack_in_room(
            client, owner_headers, room_id
        )

        resp = client.get(
            f"/api/v1/racks/{rack_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["rack_id"] == rack_id
        assert data["device_power_watts"] == 0
        assert data["power_capacity_kw"] == 10.0
        assert data["allocated_power_kw"] == 0.0

    def test_rack_power_with_devices(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        rack_id = create_rack_in_room(
            client, owner_headers, room_id
        )

        client.post(
            f"/api/v1/racks/{rack_id}/devices",
            json={
                "name": "SRV-01",
                "device_type": "SERVER",
                "status": "ACTIVE",
                "rack_unit_height": 1,
                "power_consumption_watt": 500,
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/racks/{rack_id}/devices",
            json={
                "name": "SRV-02",
                "device_type": "SERVER",
                "status": "ACTIVE",
                "rack_unit_height": 1,
                "power_consumption_watt": 300,
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/racks/{rack_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["device_power_watts"] == 800
        assert data["allocated_power_kw"] == 0.8

    def test_rack_power_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/racks/{fake_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestRoomPower:
    def test_room_power_empty(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["room_id"] == room_id
        assert data["total_ups_capacity_kva"] == 0
        assert data["total_pdu_capacity_amp"] == 0
        assert data["ups_count"] == 0
        assert data["pdu_count"] == 0

    def test_room_power_with_equipment(
        self, client, owner_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-RP",
                "capacity_kva": 5.0,
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-RP",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/rooms/{room_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_ups_capacity_kva"] == 5.0
        assert data["total_pdu_capacity_amp"] == 30.0
        assert data["ups_count"] == 1
        assert data["pdu_count"] == 1


class TestDataCenterPower:
    def test_dc_power_empty(
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
            f"/api/v1/datacenters/{dc_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["datacenter_id"] == dc_id
        assert data["total_ups_capacity_kva"] == 0
        assert data["room_count"] == 0

    def test_dc_power_with_rooms(
        self, client, owner_headers
    ):
        dc_id, room_id = create_room_chain(
            client, owner_headers
        )
        client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-DC",
                "capacity_kva": 10.0,
            },
            headers=owner_headers,
        )
        client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-DC",
                "total_capacity_amp": 60.0,
            },
            headers=owner_headers,
        )

        resp = client.get(
            f"/api/v1/datacenters/{dc_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_ups_capacity_kva"] == 10.0
        assert data["total_pdu_capacity_amp"] == 60.0
        assert data["room_count"] >= 1
        assert data["ups_count"] == 1
        assert data["pdu_count"] == 1

    def test_dc_power_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/datacenters/{fake_id}/power",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# =====================================================
# RBAC Tests
# =====================================================


class TestPowerRBAC:
    def test_viewer_cannot_create_ups(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-V",
                "capacity_kva": 3.0,
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_pdu(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-V",
                "total_capacity_amp": 30.0,
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_can_read_ups(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-R",
                "capacity_kva": 3.0,
            },
            headers=owner_headers,
        )
        ups_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/ups/{ups_id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_can_read_pdu(
        self, client, owner_headers, viewer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        create_resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-R",
                "total_capacity_amp": 30.0,
            },
            headers=owner_headers,
        )
        pdu_id = create_resp.json()["id"]

        resp = client.get(
            f"/api/v1/pdus/{pdu_id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_admin_can_create_ups(
        self, client, owner_headers, admin_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/ups",
            json={
                "name": "UPS-A",
                "capacity_kva": 3.0,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_engineer_can_create_pdu(
        self, client, owner_headers, engineer_headers
    ):
        _, room_id = create_room_chain(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room_id}/pdus",
            json={
                "name": "PDU-E",
                "total_capacity_amp": 30.0,
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_unauthenticated_returns_401(
        self, client
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/rooms/{fake_id}/ups",
        )
        assert resp.status_code == 401
