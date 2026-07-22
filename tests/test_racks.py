import uuid

from tests.conftest import (
    create_building,
    create_dc,
    create_floor,
    create_rack,
    create_room,
)


class TestCreateRack:
    def _setup_room(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        return dc, building, floor, room

    def test_create_rack_success(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
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
                "manufacturer": "APC",
                "model": "NetShelter",
                "serial_number": f"SN-{uid}",
                "position_in_room": 1,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == f"Rack-{uid}"
        assert data["rack_type"] == "SERVER_RACK"
        assert data["room_id"] == room["id"]
        assert data["height_units"] == 42
        assert data["max_weight_kg"] == 800.0
        assert data["current_weight_kg"] == 200.0
        assert data["power_capacity_kw"] == 10.0
        assert data["current_power_usage_kw"] == 3.0
        assert data["manufacturer"] == "APC"
        assert data["serial_number"] == f"SN-{uid}"

    def test_create_rack_defaults(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": f"Default-{uid}",
                "code": f"DF{uid[:4].upper()}",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rack_type"] == "SERVER_RACK"
        assert data["status"] == "ACTIVE"
        assert data["height_units"] == 42
        assert data["current_weight_kg"] == 0
        assert data["current_power_usage_kw"] == 0

    def test_create_rack_all_types(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        for rt in [
            "SERVER_RACK",
            "NETWORK_RACK",
            "STORAGE_RACK",
            "OPEN_FRAME_RACK",
            "CUSTOM",
        ]:
            uid = uuid.uuid4().hex[:4]
            resp = client.post(
                f"/api/v1/rooms/{room['id']}/racks",
                json={
                    "name": f"R-{rt}-{uid}",
                    "code": f"RT{uid.upper()}",
                    "rack_type": rt,
                },
                headers=owner_headers,
            )
            assert resp.status_code == 201
            assert resp.json()["rack_type"] == rt

    def test_create_rack_24u(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": f"Small-{uid}",
                "code": f"SM{uid[:4].upper()}",
                "height_units": 24,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["height_units"] == 24

    def test_create_rack_admin_can_create(
        self, client, admin_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, admin_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": f"Admin-{uid}",
                "code": f"AD{uid[:4].upper()}",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_create_rack_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": f"Eng-{uid}",
                "code": f"EN{uid[:4].upper()}",
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_create_rack_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": f"Vw-{uid}",
                "code": f"VW{uid[:4].upper()}",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_create_rack_no_auth(self, client):
        resp = client.post(
            "/api/v1/rooms/00000000-0000-0000-0000-000000000000/racks",
            json={"name": "No Auth", "code": "NA01"},
        )
        assert resp.status_code == 401

    def test_create_rack_duplicate_name(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Duplicate", "code": "DUP1"},
        )
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={"name": "Duplicate", "code": "DUP2"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_rack_duplicate_code(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Rack1", "code": "DUPC"},
        )
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={"name": "Rack2", "code": "DUPC"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_rack_duplicate_serial(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={
                "name": "Rack1",
                "code": "RK01",
                "serial_number": "UNIQUE-SN-001",
            },
        )
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": "Rack2",
                "code": "RK02",
                "serial_number": "UNIQUE-SN-001",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_rack_invalid_room(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/rooms/{fake_id}/racks",
            json={"name": "Bad", "code": "BD01"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_rack_missing_required(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_rack_invalid_status(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": "Bad",
                "code": "BS01",
                "status": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_rack_weight_exceeds_max(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": "Heavy",
                "code": "HV01",
                "max_weight_kg": 100.0,
                "current_weight_kg": 200.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_rack_power_exceeds_capacity(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/rooms/{room['id']}/racks",
            json={
                "name": "Overpower",
                "code": "OP01",
                "power_capacity_kw": 5.0,
                "current_power_usage_kw": 10.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


class TestListRacks:
    def _setup_room(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        return dc, building, floor, room

    def test_list_racks_empty(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["racks"] == []
        assert data["total"] == 0
        assert data["pages"] == 0

    def test_list_racks_with_data(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(client, owner_headers, room["id"])
        create_rack(client, owner_headers, room["id"])
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
        assert len(resp.json()["racks"]) == 2

    def test_list_racks_pagination(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        for _ in range(5):
            create_rack(client, owner_headers, room["id"])
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks?page=1&size=2",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["racks"]) == 2
        assert data["pages"] == 3

    def test_list_racks_filter_status(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "R1", "code": "R01", "status": "ACTIVE"},
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "R2", "code": "R02", "status": "FULL"},
        )
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks?status=ACTIVE",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["racks"][0]["status"] == "ACTIVE"

    def test_list_racks_filter_rack_type(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "SR", "code": "SR01", "rack_type": "SERVER_RACK"},
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "NR", "code": "NR01", "rack_type": "NETWORK_RACK"},
        )
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks?rack_type=SERVER_RACK",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["racks"][0]["rack_type"] == "SERVER_RACK"

    def test_list_racks_search(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Alpha Rack", "code": "AL01"},
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Beta Rack", "code": "BT01"},
        )
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks?search=Alpha",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_racks_sort(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Zulu", "code": "ZL01"},
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Alpha", "code": "AL01"},
        )
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks?sort_by=name&sort_order=asc",
            headers=owner_headers,
        )
        names = [r["name"] for r in resp.json()["racks"]]
        assert names == ["Alpha", "Zulu"]

    def test_list_racks_viewer_can_read(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Viewer", "code": "VW01"},
        )
        resp = client.get(
            f"/api/v1/rooms/{room['id']}/racks",
            headers=viewer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestGetRack:
    def _setup_room(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        return dc, building, floor, room

    def test_get_rack_success(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.get(
            f"/api/v1/racks/{rack['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == rack["id"]

    def test_get_rack_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/racks/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_get_rack_other_company(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
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
        other_token = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other-{uid}@test.com",
                "password": "testpass123",
            },
        ).json()["access_token"]
        other_headers = {
            "Authorization": f"Bearer {other_token}"
        }
        resp = client.get(
            f"/api/v1/racks/{rack['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404

    def test_get_rack_deleted_returns_404(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=owner_headers,
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestRackCapacity:
    def _setup_room(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        return dc, building, floor, room

    def test_capacity_success(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(
            client, owner_headers, room["id"],
            overrides={
                "height_units": 42,
                "max_weight_kg": 800.0,
                "current_weight_kg": 200.0,
                "power_capacity_kw": 10.0,
                "current_power_usage_kw": 3.0,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/capacity",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_u"] == 42
        assert data["used_u"] == 21
        assert data["available_u"] == 21
        assert data["power_capacity_kw"] == 10.0
        assert data["used_power_kw"] == 3.0
        assert data["available_power_kw"] == 7.0
        assert data["weight_capacity_kg"] == 800.0
        assert data["used_weight_kg"] == 200.0
        assert data["available_weight_kg"] == 600.0

    def test_capacity_no_limits(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(
            client, owner_headers, room["id"],
            overrides={
                "height_units": 42,
                "max_weight_kg": None,
                "current_weight_kg": 0,
                "power_capacity_kw": None,
                "current_power_usage_kw": 0,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/capacity",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_u"] == 42
        assert data["used_u"] == 21
        assert data["available_u"] == 21
        assert data["power_capacity_kw"] is None
        assert data["used_power_kw"] == 0
        assert data["available_power_kw"] is None
        assert data["weight_capacity_kg"] is None
        assert data["used_weight_kg"] == 0
        assert data["available_weight_kg"] is None

    def test_capacity_24u(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(
            client, owner_headers, room["id"],
            overrides={"height_units": 24},
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/capacity",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_u"] == 24
        assert data["used_u"] == 12
        assert data["available_u"] == 12

    def test_capacity_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/racks/{fake_id}/capacity",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestUpdateRack:
    def _setup_room(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        return dc, building, floor, room

    def test_update_rack_name(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.patch(
            f"/api/v1/racks/{rack['id']}",
            json={"name": "Updated Name"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_update_rack_multiple_fields(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.patch(
            f"/api/v1/racks/{rack['id']}",
            json={
                "name": "New Name",
                "code": "NEWC",
                "rack_type": "NETWORK_RACK",
                "status": "FULL",
                "height_units": 24,
                "max_weight_kg": 500.0,
                "current_weight_kg": 100.0,
                "power_capacity_kw": 8.0,
                "current_power_usage_kw": 2.0,
                "manufacturer": "Dell",
                "serial_number": "NEW-SN-001",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["rack_type"] == "NETWORK_RACK"
        assert data["status"] == "FULL"
        assert data["manufacturer"] == "Dell"

    def test_update_rack_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/racks/{fake_id}",
            json={"name": "Nope"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_rack_duplicate_name(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        r1 = create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Rack1", "code": "R101"},
        )
        r2 = create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Rack2", "code": "R201"},
        )
        resp = client.patch(
            f"/api/v1/racks/{r2['id']}",
            json={"name": "Rack1"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_rack_duplicate_serial(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        r1 = create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "R1", "code": "R01", "serial_number": "SN-001"},
        )
        r2 = create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "R2", "code": "R02", "serial_number": "SN-002"},
        )
        resp = client.patch(
            f"/api/v1/racks/{r2['id']}",
            json={"serial_number": "SN-001"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_rack_weight_validation(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(
            client, owner_headers, room["id"],
            overrides={
                "max_weight_kg": 500.0,
                "current_weight_kg": 100.0,
            },
        )
        resp = client.patch(
            f"/api/v1/racks/{rack['id']}",
            json={"current_weight_kg": 600.0},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_update_rack_power_validation(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(
            client, owner_headers, room["id"],
            overrides={
                "power_capacity_kw": 5.0,
                "current_power_usage_kw": 1.0,
            },
        )
        resp = client.patch(
            f"/api/v1/racks/{rack['id']}",
            json={"current_power_usage_kw": 8.0},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_update_rack_admin_can_update(
        self, client, admin_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, admin_headers
        )
        rack = create_rack(client, admin_headers, room["id"])
        resp = client.patch(
            f"/api/v1/racks/{rack['id']}",
            json={"name": "Admin Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Admin Updated"

    def test_update_rack_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.patch(
            f"/api/v1/racks/{rack['id']}",
            json={"name": "Eng"},
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_update_rack_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.patch(
            f"/api/v1/racks/{rack['id']}",
            json={"name": "Vw"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestDeleteRack:
    def _setup_room(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        return dc, building, floor, room

    def test_delete_rack_success(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == (
            "Rack deleted successfully"
        )
        get_resp = client.get(
            f"/api/v1/racks/{rack['id']}",
            headers=owner_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_rack_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/racks/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_rack_admin_can_delete(
        self, client, admin_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, admin_headers
        )
        rack = create_rack(client, admin_headers, room["id"])
        resp = client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_delete_rack_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_delete_rack_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        resp = client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_delete_rack_twice_returns_404(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
        client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=owner_headers,
        )
        resp = client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_rack_other_company(
        self, client, owner_headers
    ):
        dc, building, floor, room = self._setup_room(
            client, owner_headers
        )
        rack = create_rack(client, owner_headers, room["id"])
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
        other_token = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other-{uid}@test.com",
                "password": "testpass123",
            },
        ).json()["access_token"]
        other_headers = {
            "Authorization": f"Bearer {other_token}"
        }
        resp = client.delete(
            f"/api/v1/racks/{rack['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404
