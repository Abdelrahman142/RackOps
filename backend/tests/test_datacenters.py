import uuid

import pytest


# ── CREATE ──────────────────────────────────────────


class TestDataCenterCreate:
    def test_create_success(
        self, client, owner_headers, dc_payload
    ):
        resp = client.post(
            "/api/v1/datacenters",
            json=dc_payload,
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == dc_payload["name"]
        assert data["code"] == dc_payload["code"]
        assert data["status"] == "ACTIVE"
        assert "id" in data
        assert "company_id" in data

    def test_create_defaults(
        self, client, owner_headers
    ):
        resp = client.post(
            "/api/v1/datacenters",
            json={
                "name": "Minimal DC",
                "code": "MIN1",
                "country": "US",
                "city": "LA",
                "address": "1 St",
                "timezone": "America/Los_Angeles",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "PLANNED"

    def test_create_duplicate_name(
        self, client, owner_headers, dc_payload
    ):
        client.post(
            "/api/v1/datacenters",
            json=dc_payload,
            headers=owner_headers,
        )
        payload2 = {**dc_payload, "code": "USE2"}
        resp = client.post(
            "/api/v1/datacenters",
            json=payload2,
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_duplicate_code(
        self, client, owner_headers, dc_payload
    ):
        client.post(
            "/api/v1/datacenters",
            json=dc_payload,
            headers=owner_headers,
        )
        payload2 = {**dc_payload, "name": "US-West-1"}
        resp = client.post(
            "/api/v1/datacenters",
            json=payload2,
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_invalid_timezone(
        self, client, owner_headers, dc_payload
    ):
        payload = {
            **dc_payload,
            "timezone": "Invalid/Timezone",
        }
        resp = client.post(
            "/api/v1/datacenters",
            json=payload,
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_invalid_latitude(
        self, client, owner_headers, dc_payload
    ):
        payload = {**dc_payload, "latitude": 999.0}
        resp = client.post(
            "/api/v1/datacenters",
            json=payload,
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_invalid_longitude(
        self, client, owner_headers, dc_payload
    ):
        payload = {**dc_payload, "longitude": 999.0}
        resp = client.post(
            "/api/v1/datacenters",
            json=payload,
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_invalid_status(
        self, client, owner_headers, dc_payload
    ):
        payload = {
            **dc_payload,
            "status": "INVALID",
        }
        resp = client.post(
            "/api/v1/datacenters",
            json=payload,
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_viewer_forbidden(
        self, client, viewer_headers, dc_payload
    ):
        resp = client.post(
            "/api/v1/datacenters",
            json=dc_payload,
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_create_engineer_forbidden(
        self, client, engineer_headers, dc_payload
    ):
        resp = client.post(
            "/api/v1/datacenters",
            json=dc_payload,
            headers=engineer_headers,
        )
        assert resp.status_code == 403

    def test_create_admin_allowed(
        self, client, admin_headers, dc_payload
    ):
        resp = client.post(
            "/api/v1/datacenters",
            json=dc_payload,
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_create_no_auth(self, client, dc_payload):
        resp = client.post(
            "/api/v1/datacenters",
            json=dc_payload,
        )
        assert resp.status_code == 401

    def test_create_empty_name(
        self, client, owner_headers, dc_payload
    ):
        payload = {**dc_payload, "name": ""}
        resp = client.post(
            "/api/v1/datacenters",
            json=payload,
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_long_name(
        self, client, owner_headers, dc_payload
    ):
        payload = {**dc_payload, "name": "A" * 256}
        resp = client.post(
            "/api/v1/datacenters",
            json=payload,
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ── GET SINGLE ──────────────────────────────────────


class TestDataCenterGet:
    def test_get_success(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == dc["id"]

    def test_get_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/datacenters/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_get_other_company(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)

        other_data = {
            "company_name": f"Other-{uuid.uuid4().hex[:6]}",
            "company_email": f"o-{uuid.uuid4().hex[:6]}@x.com",
            "name": "Other",
            "email": f"o-{uuid.uuid4().hex[:6]}@x.com",
            "password": "testpass123",
        }
        client.post(
            "/api/v1/auth/register", json=other_data
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": other_data["email"],
                "password": "testpass123",
            },
        )
        other_headers = {
            "Authorization": f"Bearer {other_login.json()['access_token']}"
        }

        resp = client.get(
            f"/api/v1/datacenters/{dc['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404


# ── LIST ────────────────────────────────────────────


class TestDataCenterList:
    def test_list_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/datacenters",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["datacenters"] == []

    def test_list_with_data(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        create_dc(client, owner_headers)
        create_dc(client, owner_headers)
        resp = client.get(
            "/api/v1/datacenters",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_filter_by_status(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        create_dc(
            client,
            owner_headers,
            overrides={"status": "ACTIVE"},
        )
        create_dc(
            client,
            owner_headers,
            overrides={"status": "OFFLINE"},
        )
        resp = client.get(
            "/api/v1/datacenters?status=ACTIVE",
            headers=owner_headers,
        )
        assert resp.json()["total"] == 1
        assert (
            resp.json()["datacenters"][0]["status"]
            == "ACTIVE"
        )

    def test_filter_by_country(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        create_dc(
            client,
            owner_headers,
            overrides={"country": "US"},
        )
        create_dc(
            client,
            owner_headers,
            overrides={"country": "Germany"},
        )
        resp = client.get(
            "/api/v1/datacenters?country=Germany",
            headers=owner_headers,
        )
        assert resp.json()["total"] == 1
        assert (
            resp.json()["datacenters"][0]["country"]
            == "Germany"
        )

    def test_search_by_name(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        create_dc(
            client,
            owner_headers,
            overrides={"name": "Production Alpha"},
        )
        create_dc(
            client,
            owner_headers,
            overrides={"name": "Test Beta"},
        )
        resp = client.get(
            "/api/v1/datacenters?search=Alpha",
            headers=owner_headers,
        )
        assert resp.json()["total"] == 1

    def test_pagination(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        for _ in range(5):
            create_dc(client, owner_headers)

        resp = client.get(
            "/api/v1/datacenters?page=1&size=2",
            headers=owner_headers,
        )
        data = resp.json()
        assert len(data["datacenters"]) == 2
        assert data["total"] == 5
        assert data["pages"] == 3

    def test_sort_asc(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        create_dc(
            client,
            owner_headers,
            overrides={"name": "Zulu"},
        )
        create_dc(
            client,
            owner_headers,
            overrides={"name": "Alpha"},
        )
        resp = client.get(
            "/api/v1/datacenters?sort_by=name&sort_order=asc",
            headers=owner_headers,
        )
        names = [
            dc["name"]
            for dc in resp.json()["datacenters"]
        ]
        assert names == sorted(names)

    def test_invalid_sort_field(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/datacenters?sort_by=invalid",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_engineer_can_list(
        self, client, engineer_headers
    ):
        resp = client.get(
            "/api/v1/datacenters",
            headers=engineer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_can_list(
        self, client, viewer_headers
    ):
        resp = client.get(
            "/api/v1/datacenters",
            headers=viewer_headers,
        )
        assert resp.status_code == 200


# ── UPDATE ──────────────────────────────────────────


class TestDataCenterUpdate:
    def test_update_name(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.patch(
            f"/api/v1/datacenters/{dc['id']}",
            json={"name": "Updated Name"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_update_status(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.patch(
            f"/api/v1/datacenters/{dc['id']}",
            json={"status": "MAINTENANCE"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "MAINTENANCE"

    def test_update_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/datacenters/{fake_id}",
            json={"name": "X"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_duplicate_name(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc1 = create_dc(
            client,
            owner_headers,
            overrides={"name": "First DC"},
        )
        dc2 = create_dc(
            client,
            owner_headers,
            overrides={"name": "Second DC"},
        )
        resp = client.patch(
            f"/api/v1/datacenters/{dc2['id']}",
            json={"name": "First DC"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_invalid_timezone(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.patch(
            f"/api/v1/datacenters/{dc['id']}",
            json={"timezone": "Bad/Zone"},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_update_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.patch(
            f"/api/v1/datacenters/{dc['id']}",
            json={"name": "Nope"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_update_admin_allowed(
        self, client, admin_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, admin_headers)
        resp = client.patch(
            f"/api/v1/datacenters/{dc['id']}",
            json={"name": "Admin Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_update_engineer_forbidden(
        self, client, owner_headers, engineer_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.patch(
            f"/api/v1/datacenters/{dc['id']}",
            json={"name": "Nope"},
            headers=engineer_headers,
        )
        assert resp.status_code == 403


# ── DELETE ──────────────────────────────────────────


class TestDataCenterDelete:
    def test_delete_success(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.delete(
            f"/api/v1/datacenters/{dc['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

        get_resp = client.get(
            f"/api/v1/datacenters/{dc['id']}",
            headers=owner_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_not_in_list(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        client.delete(
            f"/api/v1/datacenters/{dc['id']}",
            headers=owner_headers,
        )
        resp = client.get(
            "/api/v1/datacenters",
            headers=owner_headers,
        )
        assert resp.json()["total"] == 0

    def test_delete_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/datacenters/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)
        resp = client.delete(
            f"/api/v1/datacenters/{dc['id']}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_delete_admin_allowed(
        self, client, admin_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, admin_headers)
        resp = client.delete(
            f"/api/v1/datacenters/{dc['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ── MULTI-TENANT ISOLATION ──────────────────────────


class TestDataCenterIsolation:
    def test_company_cannot_see_other_data(
        self, client, owner_headers
    ):
        from tests.conftest import create_dc

        dc = create_dc(client, owner_headers)

        other_data = {
            "company_name": f"Rival-{uuid.uuid4().hex[:6]}",
            "company_email": f"r-{uuid.uuid4().hex[:6]}@x.com",
            "name": "Rival",
            "email": f"r-{uuid.uuid4().hex[:6]}@x.com",
            "password": "testpass123",
        }
        client.post(
            "/api/v1/auth/register", json=other_data
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": other_data["email"],
                "password": "testpass123",
            },
        )
        other_h = {
            "Authorization": f"Bearer {other_login.json()['access_token']}"
        }

        list_resp = client.get(
            "/api/v1/datacenters", headers=other_h
        )
        assert list_resp.json()["total"] == 0

        get_resp = client.get(
            f"/api/v1/datacenters/{dc['id']}",
            headers=other_h,
        )
        assert get_resp.status_code == 404

        del_resp = client.delete(
            f"/api/v1/datacenters/{dc['id']}",
            headers=other_h,
        )
        assert del_resp.status_code == 404

        upd_resp = client.patch(
            f"/api/v1/datacenters/{dc['id']}",
            json={"name": "Hacked"},
            headers=other_h,
        )
        assert upd_resp.status_code == 404
