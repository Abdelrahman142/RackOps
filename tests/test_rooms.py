import uuid

from tests.conftest import (
    create_building,
    create_dc,
    create_floor,
    create_room,
)


class TestCreateRoom:
    def _setup_floor(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        return dc, building, floor

    def test_create_room_success(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": f"Room-{uid}",
                "code": f"RM{uid[:4].upper()}",
                "room_type": "SERVER_ROOM",
                "status": "ACTIVE",
                "area_sqm": 120.5,
                "height_meters": 3.2,
                "max_rack_capacity": 20,
                "max_power_capacity_kw": 100.0,
                "max_cooling_capacity_kw": 80.0,
                "temperature_min": 18.0,
                "temperature_max": 27.0,
                "humidity_min": 40.0,
                "humidity_max": 60.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == f"Room-{uid}"
        assert data["room_type"] == "SERVER_ROOM"
        assert data["floor_id"] == floor["id"]
        assert data["area_sqm"] == 120.5
        assert data["max_rack_capacity"] == 20
        assert data["temperature_min"] == 18.0
        assert data["temperature_max"] == 27.0
        assert data["humidity_min"] == 40.0
        assert data["humidity_max"] == 60.0

    def test_create_room_defaults(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": f"Default-{uid}",
                "code": f"DF{uid[:4].upper()}",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PLANNED"
        assert data["room_type"] == "SERVER_ROOM"
        assert data["area_sqm"] is None
        assert data["max_rack_capacity"] is None

    def test_create_room_all_types(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        for rt in [
            "SERVER_ROOM",
            "NETWORK_ROOM",
            "STORAGE_ROOM",
            "UPS_ROOM",
            "CONTROL_ROOM",
            "OTHER",
        ]:
            uid = uuid.uuid4().hex[:4]
            resp = client.post(
                f"/api/v1/floors/{floor['id']}/rooms",
                json={
                    "name": f"R-{rt}-{uid}",
                    "code": f"RT{uid.upper()}",
                    "room_type": rt,
                },
                headers=owner_headers,
            )
            assert resp.status_code == 201
            assert resp.json()["room_type"] == rt

    def test_create_room_admin_can_create(
        self, client, admin_headers
    ):
        dc, building, floor = self._setup_floor(
            client, admin_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": f"Admin-{uid}",
                "code": f"AD{uid[:4].upper()}",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_create_room_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": f"Eng-{uid}",
                "code": f"EN{uid[:4].upper()}",
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_create_room_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": f"Vw-{uid}",
                "code": f"VW{uid[:4].upper()}",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_create_room_no_auth(self, client):
        resp = client.post(
            "/api/v1/floors/00000000-0000-0000-0000-000000000000/rooms",
            json={"name": "No Auth", "code": "NA01"},
        )
        assert resp.status_code == 401

    def test_create_room_duplicate_name(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(
            client,
            owner_headers,
            floor["id"],
            overrides={
                "name": "Duplicate",
                "code": "DUP1",
            },
        )
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": "Duplicate",
                "code": "DUP2",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_room_duplicate_code(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(
            client,
            owner_headers,
            floor["id"],
            overrides={
                "name": "Room1",
                "code": "DUPC",
            },
        )
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": "Room2",
                "code": "DUPC",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_room_invalid_floor(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/floors/{fake_id}/rooms",
            json={"name": "Bad", "code": "BD01"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_room_missing_required(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_room_invalid_status(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": "Bad",
                "code": "BS01",
                "status": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_room_invalid_room_type(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": "Bad Type",
                "code": "BT01",
                "room_type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_room_temperature_min_gt_max(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": "Bad Temp",
                "code": "TMP1",
                "temperature_min": 30.0,
                "temperature_max": 20.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_room_humidity_min_gt_max(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/floors/{floor['id']}/rooms",
            json={
                "name": "Bad Hum",
                "code": "HUM1",
                "humidity_min": 80.0,
                "humidity_max": 30.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_room_same_name_different_floor(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        b = create_building(client, owner_headers, dc["id"])
        f1 = create_floor(
            client, owner_headers, b["id"],
            overrides={"name": "F1", "code": "FL01", "floor_number": 1},
        )
        f2 = create_floor(
            client, owner_headers, b["id"],
            overrides={"name": "F2", "code": "FL02", "floor_number": 2},
        )
        create_room(
            client, owner_headers, f1["id"],
            overrides={"name": "Same", "code": "SM01"},
        )
        resp = client.post(
            f"/api/v1/floors/{f2['id']}/rooms",
            json={"name": "Same", "code": "SM02"},
            headers=owner_headers,
        )
        assert resp.status_code == 201


class TestListRooms:
    def _setup_floor(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        return dc, building, floor

    def test_list_rooms_empty(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["rooms"] == []
        assert data["total"] == 0
        assert data["pages"] == 0

    def test_list_rooms_with_data(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(client, owner_headers, floor["id"])
        create_room(client, owner_headers, floor["id"])
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["rooms"]) == 2

    def test_list_rooms_pagination(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        for _ in range(5):
            create_room(client, owner_headers, floor["id"])
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms?page=1&size=2",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["rooms"]) == 2
        assert data["pages"] == 3

    def test_list_rooms_filter_status(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "R1", "code": "R01", "status": "ACTIVE"},
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "R2", "code": "R02", "status": "MAINTENANCE"},
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms?status=ACTIVE",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["rooms"][0]["status"] == "ACTIVE"

    def test_list_rooms_filter_room_type(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={
                "name": "Server",
                "code": "SR01",
                "room_type": "SERVER_ROOM",
            },
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={
                "name": "Network",
                "code": "NR01",
                "room_type": "NETWORK_ROOM",
            },
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms?room_type=SERVER_ROOM",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["rooms"][0]["room_type"] == "SERVER_ROOM"

    def test_list_rooms_search(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Alpha Room", "code": "AL01"},
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Beta Room", "code": "BT01"},
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms?search=Alpha",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["rooms"][0]["name"] == "Alpha Room"

    def test_list_rooms_sort(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Zulu", "code": "ZL01"},
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Alpha", "code": "AL01"},
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms?sort_by=name&sort_order=asc",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["rooms"]]
        assert names == ["Alpha", "Zulu"]

    def test_list_rooms_invalid_status_filter(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms?status=BADSTATUS",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_rooms_invalid_room_type_filter(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms?room_type=BADTYPE",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_rooms_viewer_can_read(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Viewer", "code": "VW01"},
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}/rooms",
            headers=viewer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_rooms_isolation(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        b = create_building(client, owner_headers, dc["id"])
        f1 = create_floor(
            client, owner_headers, b["id"],
            overrides={"name": "F1", "code": "FL01", "floor_number": 1},
        )
        f2 = create_floor(
            client, owner_headers, b["id"],
            overrides={"name": "F2", "code": "FL02", "floor_number": 2},
        )
        create_room(
            client, owner_headers, f1["id"],
            overrides={"name": "F1-Room", "code": "F1R1"},
        )
        create_room(
            client, owner_headers, f2["id"],
            overrides={"name": "F2-Room", "code": "F2R1"},
        )
        r1 = client.get(
            f"/api/v1/floors/{f1['id']}/rooms",
            headers=owner_headers,
        )
        r2 = client.get(
            f"/api/v1/floors/{f2['id']}/rooms",
            headers=owner_headers,
        )
        assert r1.json()["total"] == 1
        assert r1.json()["rooms"][0]["name"] == "F1-Room"
        assert r2.json()["total"] == 1
        assert r2.json()["rooms"][0]["name"] == "F2-Room"


class TestGetRoom:
    def _setup_floor(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        return dc, building, floor

    def test_get_room_success(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.get(
            f"/api/v1/rooms/{room['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == room["id"]
        assert resp.json()["name"] == room["name"]

    def test_get_room_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/rooms/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_get_room_other_company(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
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
            f"/api/v1/rooms/{room['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404

    def test_get_room_deleted_returns_404(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        client.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=owner_headers,
        )
        resp = client.get(
            f"/api/v1/rooms/{room['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestUpdateRoom:
    def _setup_floor(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        return dc, building, floor

    def test_update_room_name(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={"name": "Updated Name"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["code"] == room["code"]

    def test_update_room_multiple_fields(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={
                "name": "New Name",
                "code": "NEWC",
                "room_type": "NETWORK_ROOM",
                "status": "MAINTENANCE",
                "area_sqm": 300.0,
                "max_rack_capacity": 50,
                "temperature_min": 15.0,
                "temperature_max": 30.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["code"] == "NEWC"
        assert data["room_type"] == "NETWORK_ROOM"
        assert data["status"] == "MAINTENANCE"
        assert data["area_sqm"] == 300.0
        assert data["max_rack_capacity"] == 50
        assert data["temperature_min"] == 15.0
        assert data["temperature_max"] == 30.0

    def test_update_room_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/rooms/{fake_id}",
            json={"name": "Nope"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_room_duplicate_name(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        r1 = create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Room1", "code": "R101"},
        )
        r2 = create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Room2", "code": "R201"},
        )
        resp = client.patch(
            f"/api/v1/rooms/{r2['id']}",
            json={"name": "Room1"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_room_duplicate_code(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        r1 = create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Room1", "code": "R101"},
        )
        r2 = create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "Room2", "code": "R201"},
        )
        resp = client.patch(
            f"/api/v1/rooms/{r2['id']}",
            json={"code": "R101"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_room_temperature_validation(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={
                "temperature_min": 40.0,
                "temperature_max": 20.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_update_room_humidity_validation(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={
                "humidity_min": 90.0,
                "humidity_max": 20.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_update_room_admin_can_update(
        self, client, admin_headers
    ):
        dc, building, floor = self._setup_floor(
            client, admin_headers
        )
        room = create_room(client, admin_headers, floor["id"])
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={"name": "Admin Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Admin Updated"

    def test_update_room_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={"name": "Eng Updated"},
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_update_room_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={"name": "Vw Updated"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_update_room_same_name_no_conflict(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(
            client, owner_headers, floor["id"],
            overrides={"name": "SameName", "code": "SN01"},
        )
        resp = client.patch(
            f"/api/v1/rooms/{room['id']}",
            json={"description": "Updated desc only"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "SameName"


class TestDeleteRoom:
    def _setup_floor(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        return dc, building, floor

    def test_delete_room_success(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == (
            "Room deleted successfully"
        )
        get_resp = client.get(
            f"/api/v1/rooms/{room['id']}",
            headers=owner_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_room_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/rooms/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_room_admin_can_delete(
        self, client, admin_headers
    ):
        dc, building, floor = self._setup_floor(
            client, admin_headers
        )
        room = create_room(client, admin_headers, floor["id"])
        resp = client.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_delete_room_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_delete_room_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        resp = client.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_delete_room_twice_returns_404(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
        client.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=owner_headers,
        )
        resp = client.delete(
            f"/api/v1/rooms/{room['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_room_other_company(
        self, client, owner_headers
    ):
        dc, building, floor = self._setup_floor(
            client, owner_headers
        )
        room = create_room(client, owner_headers, floor["id"])
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
            f"/api/v1/rooms/{room['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404
