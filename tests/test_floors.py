import uuid

from tests.conftest import (
    create_building,
    create_dc,
    create_floor,
)


class TestCreateFloor:
    def _setup_building(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(
            client, headers, dc["id"]
        )
        return dc, building

    def test_create_floor_success(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": f"Floor-{uid}",
                "code": f"FL{uid[:4].upper()}",
                "floor_number": 1,
                "status": "ACTIVE",
                "total_area_sqm": 500.0,
                "max_power_capacity_kw": 200.0,
                "max_cooling_capacity_kw": 150.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == f"Floor-{uid}"
        assert data["code"] == f"FL{uid[:4].upper()}"
        assert data["building_id"] == building["id"]
        assert data["floor_number"] == 1
        assert data["total_area_sqm"] == 500.0
        assert data["max_power_capacity_kw"] == 200.0
        assert data["max_cooling_capacity_kw"] == 150.0

    def test_create_floor_defaults(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": f"Default-{uid}",
                "code": f"DF{uid[:4].upper()}",
                "floor_number": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PLANNED"
        assert data["total_area_sqm"] is None
        assert data["max_power_capacity_kw"] is None
        assert data["max_cooling_capacity_kw"] is None

    def test_create_floor_negative_number(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": f"Basement-{uid}",
                "code": f"BM{uid[:4].upper()}",
                "floor_number": -1,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["floor_number"] == -1

    def test_create_floor_admin_can_create(
        self, client, admin_headers
    ):
        dc, building = self._setup_building(
            client, admin_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": f"Admin-{uid}",
                "code": f"AD{uid[:4].upper()}",
                "floor_number": 1,
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_create_floor_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": f"Eng-{uid}",
                "code": f"EN{uid[:4].upper()}",
                "floor_number": 1,
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_create_floor_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": f"Vw-{uid}",
                "code": f"VW{uid[:4].upper()}",
                "floor_number": 1,
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_create_floor_no_auth(self, client):
        resp = client.post(
            "/api/v1/buildings/00000000-0000-0000-0000-000000000000/floors",
            json={
                "name": "No Auth",
                "code": "NA01",
                "floor_number": 1,
            },
        )
        assert resp.status_code == 401

    def test_create_floor_duplicate_name(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Duplicate",
                "code": "DUP1",
                "floor_number": 1,
            },
        )
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": "Duplicate",
                "code": "DUP2",
                "floor_number": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_floor_duplicate_code(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor1",
                "code": "DUPC",
                "floor_number": 1,
            },
        )
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": "Floor2",
                "code": "DUPC",
                "floor_number": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_floor_duplicate_floor_number(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor1",
                "code": "FN01",
                "floor_number": 5,
            },
        )
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": "Floor2",
                "code": "FN02",
                "floor_number": 5,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_floor_invalid_building(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/buildings/{fake_id}/floors",
            json={
                "name": "Bad",
                "code": "BD01",
                "floor_number": 1,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_floor_missing_required(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_floor_invalid_status(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": "Bad Status",
                "code": "BS01",
                "floor_number": 1,
                "status": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_floor_floor_number_too_low(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/buildings/{building['id']}/floors",
            json={
                "name": "Too Low",
                "code": "TL01",
                "floor_number": -6,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_floor_same_name_different_building(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        b1 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "B1", "code": "B001"},
        )
        b2 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "B2", "code": "B002"},
        )
        create_floor(
            client,
            owner_headers,
            b1["id"],
            overrides={
                "name": "Same",
                "code": "SM01",
                "floor_number": 1,
            },
        )
        resp = client.post(
            f"/api/v1/buildings/{b2['id']}/floors",
            json={
                "name": "Same",
                "code": "SM02",
                "floor_number": 1,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201


class TestListFloors:
    def _setup_building(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(
            client, headers, dc["id"]
        )
        return dc, building

    def test_list_floors_empty(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["floors"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 0

    def test_list_floors_with_data(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(client, owner_headers, building["id"])
        create_floor(client, owner_headers, building["id"])
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["floors"]) == 2

    def test_list_floors_pagination(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        for _ in range(5):
            create_floor(
                client, owner_headers, building["id"]
            )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors?page=1&size=2",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["floors"]) == 2
        assert data["pages"] == 3

    def test_list_floors_filter_status(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Active1",
                "code": "AC1",
                "floor_number": 1,
                "status": "ACTIVE",
            },
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Maint1",
                "code": "MT1",
                "floor_number": 2,
                "status": "MAINTENANCE",
            },
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors?status=ACTIVE",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["floors"][0]["status"] == "ACTIVE"

    def test_list_floors_filter_floor_number(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "F1",
                "code": "F01",
                "floor_number": 1,
            },
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "F2",
                "code": "F02",
                "floor_number": 2,
            },
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors?floor_number=1",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["floors"][0]["floor_number"] == 1

    def test_list_floors_search(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Alpha Floor",
                "code": "AL01",
                "floor_number": 1,
            },
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Beta Floor",
                "code": "BT01",
                "floor_number": 2,
            },
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors?search=Alpha",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["floors"][0]["name"] == "Alpha Floor"

    def test_list_floors_sort(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Zulu",
                "code": "ZL01",
                "floor_number": 2,
            },
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Alpha",
                "code": "AL01",
                "floor_number": 1,
            },
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors?sort_by=name&sort_order=asc",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [f["name"] for f in data["floors"]]
        assert names == ["Alpha", "Zulu"]

    def test_list_floors_sort_by_floor_number(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "High",
                "code": "HI01",
                "floor_number": 3,
            },
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Low",
                "code": "LO01",
                "floor_number": 1,
            },
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors?sort_by=floor_number&sort_order=asc",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        nums = [
            f["floor_number"]
            for f in resp.json()["floors"]
        ]
        assert nums == [1, 3]

    def test_list_floors_invalid_status_filter(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors?status=BADSTATUS",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_floors_viewer_can_read(
        self, client, owner_headers, viewer_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Viewer Test",
                "code": "VT01",
                "floor_number": 1,
            },
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}/floors",
            headers=viewer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_floors_isolation(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        b1 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "B1", "code": "B001"},
        )
        b2 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "B2", "code": "B002"},
        )
        create_floor(
            client,
            owner_headers,
            b1["id"],
            overrides={
                "name": "B1-Floor",
                "code": "B1F1",
                "floor_number": 1,
            },
        )
        create_floor(
            client,
            owner_headers,
            b2["id"],
            overrides={
                "name": "B2-Floor",
                "code": "B2F1",
                "floor_number": 1,
            },
        )
        r1 = client.get(
            f"/api/v1/buildings/{b1['id']}/floors",
            headers=owner_headers,
        )
        r2 = client.get(
            f"/api/v1/buildings/{b2['id']}/floors",
            headers=owner_headers,
        )
        assert r1.json()["total"] == 1
        assert r1.json()["floors"][0]["name"] == "B1-Floor"
        assert r2.json()["total"] == 1
        assert r2.json()["floors"][0]["name"] == "B2-Floor"


class TestGetFloor:
    def _setup_building(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(
            client, headers, dc["id"]
        )
        return dc, building

    def test_get_floor_success(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == floor["id"]
        assert data["name"] == floor["name"]

    def test_get_floor_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/floors/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_get_floor_other_company(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
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
            f"/api/v1/floors/{floor['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404

    def test_get_floor_deleted_returns_404(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        client.delete(
            f"/api/v1/floors/{floor['id']}",
            headers=owner_headers,
        )
        resp = client.get(
            f"/api/v1/floors/{floor['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestUpdateFloor:
    def _setup_building(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(
            client, headers, dc["id"]
        )
        return dc, building

    def test_update_floor_name(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.patch(
            f"/api/v1/floors/{floor['id']}",
            json={"name": "Updated Name"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["code"] == floor["code"]

    def test_update_floor_multiple_fields(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.patch(
            f"/api/v1/floors/{floor['id']}",
            json={
                "name": "New Name",
                "code": "NEWC",
                "floor_number": 99,
                "status": "MAINTENANCE",
                "total_area_sqm": 3000.0,
                "max_power_capacity_kw": 200.0,
                "max_cooling_capacity_kw": 150.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["code"] == "NEWC"
        assert data["floor_number"] == 99
        assert data["status"] == "MAINTENANCE"
        assert data["total_area_sqm"] == 3000.0
        assert data["max_power_capacity_kw"] == 200.0
        assert data["max_cooling_capacity_kw"] == 150.0

    def test_update_floor_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/floors/{fake_id}",
            json={"name": "Nope"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_floor_duplicate_name(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        f1 = create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor1",
                "code": "F101",
                "floor_number": 1,
            },
        )
        f2 = create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor2",
                "code": "F201",
                "floor_number": 2,
            },
        )
        resp = client.patch(
            f"/api/v1/floors/{f2['id']}",
            json={"name": "Floor1"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_floor_duplicate_code(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        f1 = create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor1",
                "code": "F101",
                "floor_number": 1,
            },
        )
        f2 = create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor2",
                "code": "F201",
                "floor_number": 2,
            },
        )
        resp = client.patch(
            f"/api/v1/floors/{f2['id']}",
            json={"code": "F101"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_floor_duplicate_floor_number(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        f1 = create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor1",
                "code": "F101",
                "floor_number": 1,
            },
        )
        f2 = create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "Floor2",
                "code": "F201",
                "floor_number": 2,
            },
        )
        resp = client.patch(
            f"/api/v1/floors/{f2['id']}",
            json={"floor_number": 1},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_floor_admin_can_update(
        self, client, admin_headers
    ):
        dc, building = self._setup_building(
            client, admin_headers
        )
        floor = create_floor(
            client, admin_headers, building["id"]
        )
        resp = client.patch(
            f"/api/v1/floors/{floor['id']}",
            json={"name": "Admin Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Admin Updated"

    def test_update_floor_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.patch(
            f"/api/v1/floors/{floor['id']}",
            json={"name": "Eng Updated"},
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_update_floor_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.patch(
            f"/api/v1/floors/{floor['id']}",
            json={"name": "Vw Updated"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_update_floor_same_name_no_conflict(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client,
            owner_headers,
            building["id"],
            overrides={
                "name": "SameName",
                "code": "SN01",
                "floor_number": 1,
            },
        )
        resp = client.patch(
            f"/api/v1/floors/{floor['id']}",
            json={"description": "Updated desc only"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "SameName"


class TestDeleteFloor:
    def _setup_building(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(
            client, headers, dc["id"]
        )
        return dc, building

    def test_delete_floor_success(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.delete(
            f"/api/v1/floors/{floor['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == (
            "Floor deleted successfully"
        )
        get_resp = client.get(
            f"/api/v1/floors/{floor['id']}",
            headers=owner_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_floor_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/floors/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_floor_admin_can_delete(
        self, client, admin_headers
    ):
        dc, building = self._setup_building(
            client, admin_headers
        )
        floor = create_floor(
            client, admin_headers, building["id"]
        )
        resp = client.delete(
            f"/api/v1/floors/{floor['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_delete_floor_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.delete(
            f"/api/v1/floors/{floor['id']}",
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_delete_floor_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        resp = client.delete(
            f"/api/v1/floors/{floor['id']}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_delete_floor_twice_returns_404(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
        client.delete(
            f"/api/v1/floors/{floor['id']}",
            headers=owner_headers,
        )
        resp = client.delete(
            f"/api/v1/floors/{floor['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_floor_other_company(
        self, client, owner_headers
    ):
        dc, building = self._setup_building(
            client, owner_headers
        )
        floor = create_floor(
            client, owner_headers, building["id"]
        )
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
            f"/api/v1/floors/{floor['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404
