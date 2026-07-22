import uuid

from tests.conftest import create_building, create_dc


class TestCreateBuilding:
    def test_create_building_success(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": f"Main-{uid}",
                "code": f"MB{uid[:4].upper()}",
                "address": "123 Main St",
                "status": "ACTIVE",
                "number_of_floors": 5,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == f"Main-{uid}"
        assert data["code"] == f"MB{uid[:4].upper()}"
        assert data["datacenter_id"] == dc["id"]
        assert data["number_of_floors"] == 5
        assert data["status"] == "ACTIVE"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_building_defaults(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": f"Default-{uid}",
                "code": f"DF{uid[:4].upper()}",
                "address": "456 Default St",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PLANNED"
        assert data["number_of_floors"] == 1

    def test_create_building_optional_fields(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": f"Full-{uid}",
                "code": f"FL{uid[:4].upper()}",
                "address": "789 Full St",
                "description": "Fully loaded building",
                "status": "ACTIVE",
                "number_of_floors": 10,
                "total_area": 5000.5,
                "power_capacity_kw": 250.75,
                "cooling_capacity_kw": 180.25,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_area"] == 5000.5
        assert data["power_capacity_kw"] == 250.75
        assert data["cooling_capacity_kw"] == 180.25
        assert data["description"] == "Fully loaded building"

    def test_create_building_admin_can_create(
        self, client, admin_headers
    ):
        dc = create_dc(client, admin_headers)
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": f"Admin-{uid}",
                "code": f"AD{uid[:4].upper()}",
                "address": "Admin St",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_create_building_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc = create_dc(client, owner_headers)
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": f"Eng-{uid}",
                "code": f"EN{uid[:4].upper()}",
                "address": "Engineer St",
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_create_building_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc = create_dc(client, owner_headers)
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": f"Vw-{uid}",
                "code": f"VW{uid[:4].upper()}",
                "address": "Viewer St",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_create_building_no_auth(
        self, client
    ):
        resp = client.post(
            "/api/v1/datacenters/00000000-0000-0000-0000-000000000000/buildings",
            json={
                "name": "No Auth",
                "code": "NA01",
                "address": "Nowhere",
            },
        )
        assert resp.status_code == 401

    def test_create_building_duplicate_name(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": "Duplicate",
                "code": "DUP1",
                "address": "Dup St",
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": "Duplicate",
                "code": "DUP2",
                "address": "Dup St 2",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_building_duplicate_code(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": "Building1",
                "code": "DUPC",
                "address": "Dup St",
            },
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": "Building2",
                "code": "DUPC",
                "address": "Dup St 2",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_building_invalid_datacenter(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/datacenters/{fake_id}/buildings",
            json={
                "name": "Bad DC",
                "code": "BD01",
                "address": "Nowhere",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_building_missing_required(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_building_invalid_status(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        resp = client.post(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            json={
                "name": "Bad Status",
                "code": "BS01",
                "address": "BS St",
                "status": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


class TestListBuildings:
    def test_list_buildings_empty(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["buildings"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 0

    def test_list_buildings_with_data(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        create_building(client, owner_headers, dc["id"])
        create_building(client, owner_headers, dc["id"])
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["buildings"]) == 2

    def test_list_buildings_pagination(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        for _ in range(5):
            create_building(
                client, owner_headers, dc["id"]
            )
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings?page=1&size=2",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["buildings"]) == 2
        assert data["pages"] == 3

    def test_list_buildings_filter_status(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Active1", "code": "AC1", "status": "ACTIVE"},
        )
        create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Maint1", "code": "MT1", "status": "MAINTENANCE"},
        )
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings?status=ACTIVE",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["buildings"][0]["status"] == "ACTIVE"

    def test_list_buildings_search(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Alpha Building", "code": "AL01"},
        )
        create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Beta Building", "code": "BT01"},
        )
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings?search=Alpha",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["buildings"][0]["name"] == "Alpha Building"

    def test_list_buildings_sort(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Zulu", "code": "ZL01"},
        )
        create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Alpha", "code": "AL01"},
        )
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings?sort_by=name&sort_order=asc",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [b["name"] for b in data["buildings"]]
        assert names == ["Alpha", "Zulu"]

    def test_list_buildings_invalid_status_filter(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings?status=BADSTATUS",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_buildings_viewer_can_read(
        self, client, owner_headers, viewer_headers
    ):
        dc = create_dc(client, owner_headers)
        create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Viewer Test", "code": "VT01"},
        )
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}/buildings",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_list_buildings_isolation(
        self, client, owner_headers
    ):
        dc1 = create_dc(client, owner_headers)
        dc2 = create_dc(client, owner_headers)
        create_building(
            client,
            owner_headers,
            dc1["id"],
            overrides={"name": "DC1-Only", "code": "D101"},
        )
        create_building(
            client,
            owner_headers,
            dc2["id"],
            overrides={"name": "DC2-Only", "code": "D201"},
        )
        resp1 = client.get(
            f"/api/v1/datacenters/{dc1['id']}/buildings",
            headers=owner_headers,
        )
        resp2 = client.get(
            f"/api/v1/datacenters/{dc2['id']}/buildings",
            headers=owner_headers,
        )
        assert resp1.json()["total"] == 1
        assert resp1.json()["buildings"][0]["name"] == "DC1-Only"
        assert resp2.json()["total"] == 1
        assert resp2.json()["buildings"][0]["name"] == "DC2-Only"


class TestGetBuilding:
    def test_get_building_success(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == building["id"]
        assert data["name"] == building["name"]

    def test_get_building_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/buildings/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_get_building_other_company(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        uid = uuid.uuid4().hex[:8]
        resp2 = client.post(
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
            f"/api/v1/buildings/{building['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404

    def test_get_building_deleted_returns_404(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        client.delete(
            f"/api/v1/buildings/{building['id']}",
            headers=owner_headers,
        )
        resp = client.get(
            f"/api/v1/buildings/{building['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestUpdateBuilding:
    def test_update_building_name(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.patch(
            f"/api/v1/buildings/{building['id']}",
            json={"name": "Updated Name"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["code"] == building["code"]

    def test_update_building_multiple_fields(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.patch(
            f"/api/v1/buildings/{building['id']}",
            json={
                "name": "New Name",
                "code": "NEWC",
                "status": "MAINTENANCE",
                "number_of_floors": 8,
                "total_area": 3000.0,
                "power_capacity_kw": 200.0,
                "cooling_capacity_kw": 150.0,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["code"] == "NEWC"
        assert data["status"] == "MAINTENANCE"
        assert data["number_of_floors"] == 8
        assert data["total_area"] == 3000.0
        assert data["power_capacity_kw"] == 200.0
        assert data["cooling_capacity_kw"] == 150.0

    def test_update_building_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/buildings/{fake_id}",
            json={"name": "Nope"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_building_duplicate_name(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        b1 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Building1", "code": "B101"},
        )
        b2 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Building2", "code": "B201"},
        )
        resp = client.patch(
            f"/api/v1/buildings/{b2['id']}",
            json={"name": "Building1"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_building_duplicate_code(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        b1 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Building1", "code": "B101"},
        )
        b2 = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "Building2", "code": "B201"},
        )
        resp = client.patch(
            f"/api/v1/buildings/{b2['id']}",
            json={"code": "B101"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_building_admin_can_update(
        self, client, admin_headers
    ):
        dc = create_dc(client, admin_headers)
        building = create_building(
            client, admin_headers, dc["id"]
        )
        resp = client.patch(
            f"/api/v1/buildings/{building['id']}",
            json={"name": "Admin Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Admin Updated"

    def test_update_building_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.patch(
            f"/api/v1/buildings/{building['id']}",
            json={"name": "Engineer Updated"},
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_update_building_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.patch(
            f"/api/v1/buildings/{building['id']}",
            json={"name": "Viewer Updated"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_update_building_same_name_no_conflict(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client,
            owner_headers,
            dc["id"],
            overrides={"name": "SameName", "code": "SN01"},
        )
        resp = client.patch(
            f"/api/v1/buildings/{building['id']}",
            json={"description": "Updated desc only"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "SameName"


class TestDeleteBuilding:
    def test_delete_building_success(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.delete(
            f"/api/v1/buildings/{building['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == (
            "Building deleted successfully"
        )
        get_resp = client.get(
            f"/api/v1/buildings/{building['id']}",
            headers=owner_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_building_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/buildings/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_building_admin_can_delete(
        self, client, admin_headers
    ):
        dc = create_dc(client, admin_headers)
        building = create_building(
            client, admin_headers, dc["id"]
        )
        resp = client.delete(
            f"/api/v1/buildings/{building['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_delete_building_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.delete(
            f"/api/v1/buildings/{building['id']}",
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_delete_building_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        resp = client.delete(
            f"/api/v1/buildings/{building['id']}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_delete_building_twice_returns_404(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
        )
        client.delete(
            f"/api/v1/buildings/{building['id']}",
            headers=owner_headers,
        )
        resp = client.delete(
            f"/api/v1/buildings/{building['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_building_other_company(
        self, client, owner_headers
    ):
        dc = create_dc(client, owner_headers)
        building = create_building(
            client, owner_headers, dc["id"]
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
            f"/api/v1/buildings/{building['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404
