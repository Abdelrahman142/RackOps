import uuid

from tests.conftest import (
    create_building,
    create_dc,
    create_device,
    create_floor,
    create_rack,
    create_room,
)


class TestCreateDevice:
    def _setup_rack(
        self, client, headers, rack_overrides=None
    ):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        rack = create_rack(
            client, headers, room["id"],
            overrides=rack_overrides,
        )
        return dc, building, floor, room, rack

    def test_create_device_success(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": f"Server-{uid}",
                "hostname": f"srv-{uid}.local",
                "device_type": "SERVER",
                "status": "ACTIVE",
                "vendor": "Dell",
                "model": "PowerEdge R750",
                "serial_number": f"SN-{uid}",
                "asset_tag": f"AT-{uid}",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
                "front_or_rear": "FRONT",
                "ip_address": "192.168.1.100",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "management_ip": "10.0.0.100",
                "operating_system": "Ubuntu 22.04",
                "cpu": "2x Intel Xeon Gold 6348",
                "memory_gb": 256,
                "storage_gb": 2000,
                "power_consumption_watt": 750,
                "purchase_date": "2024-01-15",
                "warranty_end_date": "2027-01-15",
                "description": "Main web server",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == f"Server-{uid}"
        assert data["hostname"] == f"srv-{uid}.local"
        assert data["device_type"] == "SERVER"
        assert data["status"] == "ACTIVE"
        assert data["vendor"] == "Dell"
        assert data["model"] == "PowerEdge R750"
        assert data["serial_number"] == f"SN-{uid}"
        assert data["asset_tag"] == f"AT-{uid}"
        assert data["rack_id"] == rack["id"]
        assert data["rack_unit_start"] == 1
        assert data["rack_unit_height"] == 2
        assert data["front_or_rear"] == "FRONT"
        assert data["ip_address"] == "192.168.1.100"
        assert data["mac_address"] == "AA:BB:CC:DD:EE:FF"
        assert data["management_ip"] == "10.0.0.100"
        assert data["operating_system"] == "Ubuntu 22.04"
        assert data["memory_gb"] == 256
        assert data["storage_gb"] == 2000
        assert data["power_consumption_watt"] == 750

    def test_create_device_defaults(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={"name": f"Def-{uid}"},
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["device_type"] == "SERVER"
        assert data["status"] == "ACTIVE"
        assert data["rack_unit_height"] == 1
        assert data["rack_unit_start"] is None
        assert data["serial_number"] is None
        assert data["asset_tag"] is None

    def test_create_device_all_types(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        for dt in [
            "SERVER",
            "SWITCH",
            "ROUTER",
            "FIREWALL",
            "STORAGE",
            "UPS",
            "PDU",
            "LOAD_BALANCER",
            "PATCH_PANEL",
            "OTHER",
        ]:
            uid = uuid.uuid4().hex[:4]
            resp = client.post(
                f"/api/v1/racks/{rack['id']}/devices",
                json={
                    "name": f"D-{dt}-{uid}",
                    "device_type": dt,
                },
                headers=owner_headers,
            )
            assert resp.status_code == 201
            assert resp.json()["device_type"] == dt

    def test_create_device_admin_can_create(
        self, client, admin_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, admin_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={"name": f"Admin-{uid}"},
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_create_device_engineer_can_create(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={"name": f"Eng-{uid}"},
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_create_device_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={"name": f"Vw-{uid}"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_create_device_no_auth(self, client):
        resp = client.post(
            "/api/v1/racks/00000000-0000-0000-0000-000000000000/devices",
            json={"name": "No Auth"},
        )
        assert resp.status_code == 401

    def test_create_device_duplicate_name(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={"name": "DupDevice"},
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={"name": "DupDevice"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_device_duplicate_name_other_rack(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        rack2 = create_rack(
            client, owner_headers, room["id"],
            overrides={"name": "Rack2", "code": "RK02"},
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={"name": "SharedName"},
        )
        resp = client.post(
            f"/api/v1/racks/{rack2['id']}/devices",
            json={"name": "SharedName"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_device_duplicate_serial(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "serial_number": "DUP-SN-001",
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "D2",
                "serial_number": "DUP-SN-001",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_device_duplicate_asset_tag(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "asset_tag": "DUP-TAG-001",
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "D2",
                "asset_tag": "DUP-TAG-001",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_create_device_invalid_rack(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/racks/{fake_id}/devices",
            json={"name": "Bad"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_create_device_missing_required(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_invalid_status(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "Bad",
                "status": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_invalid_device_type(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "Bad",
                "device_type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_rack_unit_overlap(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "First",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "Overlap",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_rack_unit_overlap_partial(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "First",
                "rack_unit_start": 1,
                "rack_unit_height": 4,
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "OverlapPartial",
                "rack_unit_start": 3,
                "rack_unit_height": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_rack_capacity_exceeded(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "TooTall",
                "rack_unit_start": 40,
                "rack_unit_height": 5,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_power_exceeds_rack(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers,
            rack_overrides={
                "power_capacity_kw": 1.0,
                "current_power_usage_kw": 0,
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "PowerHog",
                "power_consumption_watt": 2000,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_power_cumulative(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers,
            rack_overrides={
                "power_capacity_kw": 1.0,
                "current_power_usage_kw": 0,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "P1",
                "power_consumption_watt": 800,
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "P2",
                "power_consumption_watt": 300,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_create_device_valid_placement(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp1 = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "First",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
            headers=owner_headers,
        )
        assert resp1.status_code == 201
        resp2 = client.post(
            f"/api/v1/racks/{rack['id']}/devices",
            json={
                "name": "Second",
                "rack_unit_start": 3,
                "rack_unit_height": 2,
            },
            headers=owner_headers,
        )
        assert resp2.status_code == 201


class TestListDevices:
    def _setup_rack(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        rack = create_rack(client, headers, room["id"])
        return dc, building, floor, room, rack

    def test_list_devices_empty(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["devices"] == []
        assert data["total"] == 0
        assert data["pages"] == 0

    def test_list_devices_with_data(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "rack_unit_start": 1,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D2",
                "rack_unit_start": 3,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
        assert len(resp.json()["devices"]) == 2

    def test_list_devices_pagination(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        for i in range(5):
            create_device(
                client, owner_headers, rack["id"],
                overrides={
                    "name": f"Dev{i}",
                    "rack_unit_start": i * 2 + 1,
                },
            )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices?page=1&size=2",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["devices"]) == 2
        assert data["pages"] == 3

    def test_list_devices_filter_status(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "status": "ACTIVE",
                "rack_unit_start": 1,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D2",
                "status": "FAILED",
                "rack_unit_start": 3,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices?status=ACTIVE",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["devices"][0]["status"] == "ACTIVE"

    def test_list_devices_filter_device_type(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Srv",
                "device_type": "SERVER",
                "rack_unit_start": 1,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Sw",
                "device_type": "SWITCH",
                "rack_unit_start": 3,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices?device_type=SERVER",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["devices"][0]["device_type"] == "SERVER"

    def test_list_devices_filter_vendor(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "vendor": "Dell",
                "rack_unit_start": 1,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D2",
                "vendor": "Cisco",
                "rack_unit_start": 3,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices?vendor=Dell",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_devices_search(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Alpha Server",
                "hostname": "alpha.local",
                "rack_unit_start": 1,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Beta Server",
                "hostname": "beta.local",
                "rack_unit_start": 3,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices?search=Alpha",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_devices_search_hostname(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "hostname": "web01.prod.local",
                "rack_unit_start": 1,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D2",
                "hostname": "db01.prod.local",
                "rack_unit_start": 3,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices?search=web01",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_devices_sort(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Zulu",
                "rack_unit_start": 1,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Alpha",
                "rack_unit_start": 3,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices?sort_by=name&sort_order=asc",
            headers=owner_headers,
        )
        names = [d["name"] for d in resp.json()["devices"]]
        assert names == ["Alpha", "Zulu"]

    def test_list_devices_viewer_can_read(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Viewer Device",
                "rack_unit_start": 1,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/devices",
            headers=viewer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestGetDevice:
    def _setup_rack(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        rack = create_rack(client, headers, room["id"])
        return dc, building, floor, room, rack

    def test_get_device_success(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.get(
            f"/api/v1/devices/{device['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == device["id"]
        assert resp.json()["name"] == device["name"]

    def test_get_device_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/devices/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_get_device_other_company(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
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
            f"/api/v1/devices/{device['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404

    def test_get_device_deleted_returns_404(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        client.delete(
            f"/api/v1/devices/{device['id']}",
            headers=owner_headers,
        )
        resp = client.get(
            f"/api/v1/devices/{device['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestUpdateDevice:
    def _setup_rack(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        rack = create_rack(client, headers, room["id"])
        return dc, building, floor, room, rack

    def test_update_device_name(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.patch(
            f"/api/v1/devices/{device['id']}",
            json={"name": "Updated Name"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_update_device_multiple_fields(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.patch(
            f"/api/v1/devices/{device['id']}",
            json={
                "name": "New Name",
                "hostname": "new.local",
                "device_type": "SWITCH",
                "status": "MAINTENANCE",
                "vendor": "Cisco",
                "model": "Catalyst 9300",
                "memory_gb": 128,
                "storage_gb": 500,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["hostname"] == "new.local"
        assert data["device_type"] == "SWITCH"
        assert data["status"] == "MAINTENANCE"
        assert data["vendor"] == "Cisco"

    def test_update_device_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/devices/{fake_id}",
            json={"name": "Nope"},
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_device_duplicate_name(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        d1 = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Device1",
                "rack_unit_start": 1,
            },
        )
        d2 = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Device2",
                "rack_unit_start": 10,
            },
        )
        resp = client.patch(
            f"/api/v1/devices/{d2['id']}",
            json={"name": "Device1"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_device_duplicate_serial(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        d1 = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "serial_number": "SN-001",
                "rack_unit_start": 1,
            },
        )
        d2 = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D2",
                "serial_number": "SN-002",
                "rack_unit_start": 10,
            },
        )
        resp = client.patch(
            f"/api/v1/devices/{d2['id']}",
            json={"serial_number": "SN-001"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_device_duplicate_asset_tag(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        d1 = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D1",
                "asset_tag": "TAG-001",
                "rack_unit_start": 1,
            },
        )
        d2 = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "D2",
                "asset_tag": "TAG-002",
                "rack_unit_start": 10,
            },
        )
        resp = client.patch(
            f"/api/v1/devices/{d2['id']}",
            json={"asset_tag": "TAG-001"},
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_update_device_overlap_validation(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Fixed",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
        )
        movable = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Movable",
                "rack_unit_start": 10,
                "rack_unit_height": 2,
            },
        )
        resp = client.patch(
            f"/api/v1/devices/{movable['id']}",
            json={
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_update_device_same_position_ok(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Stable",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
        )
        resp = client.patch(
            f"/api/v1/devices/{device['id']}",
            json={"rack_unit_start": 1, "rack_unit_height": 2},
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_update_device_admin_can_update(
        self, client, admin_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, admin_headers
        )
        device = create_device(
            client, admin_headers, rack["id"]
        )
        resp = client.patch(
            f"/api/v1/devices/{device['id']}",
            json={"name": "Admin Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_update_device_engineer_can_update(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.patch(
            f"/api/v1/devices/{device['id']}",
            json={"name": "Eng Updated"},
            headers=engineer_headers,
        )
        assert resp.status_code == 200

    def test_update_device_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.patch(
            f"/api/v1/devices/{device['id']}",
            json={"name": "Vw"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403


class TestDeleteDevice:
    def _setup_rack(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        rack = create_rack(client, headers, room["id"])
        return dc, building, floor, room, rack

    def test_delete_device_success(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.delete(
            f"/api/v1/devices/{device['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == (
            "Device deleted successfully"
        )
        get_resp = client.get(
            f"/api/v1/devices/{device['id']}",
            headers=owner_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_device_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/devices/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_device_admin_can_delete(
        self, client, admin_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, admin_headers
        )
        device = create_device(
            client, admin_headers, rack["id"]
        )
        resp = client.delete(
            f"/api/v1/devices/{device['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_delete_device_engineer_can_delete(
        self, client, owner_headers, engineer_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.delete(
            f"/api/v1/devices/{device['id']}",
            headers=engineer_headers,
        )
        assert resp.status_code == 200

    def test_delete_device_viewer_forbidden(
        self, client, owner_headers, viewer_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        resp = client.delete(
            f"/api/v1/devices/{device['id']}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_delete_device_twice_returns_404(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
        )
        client.delete(
            f"/api/v1/devices/{device['id']}",
            headers=owner_headers,
        )
        resp = client.delete(
            f"/api/v1/devices/{device['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_delete_device_other_company(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"]
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
            f"/api/v1/devices/{device['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404


class TestRackLayout:
    def _setup_rack(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        rack = create_rack(
            client, headers, room["id"],
            overrides={"height_units": 10},
        )
        return dc, building, floor, room, rack

    def test_layout_empty_rack(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/layout",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_units"] == 10
        assert data["used_units"] == 0
        assert data["available_units"] == 10
        assert len(data["positions"]) == 10
        assert all(
            not p["occupied"] for p in data["positions"]
        )

    def test_layout_with_devices(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Device-A",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Device-B",
                "rack_unit_start": 5,
                "rack_unit_height": 1,
            },
        )
        resp = client.get(
            f"/api/v1/racks/{rack['id']}/layout",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["used_units"] == 3
        assert data["available_units"] == 7
        occupied = [
            p for p in data["positions"] if p["occupied"]
        ]
        assert len(occupied) == 3

    def test_layout_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/racks/{fake_id}/layout",
            headers=owner_headers,
        )
        assert resp.status_code == 404


class TestCheckPlacement:
    def _setup_rack(self, client, headers):
        dc = create_dc(client, headers)
        building = create_building(client, headers, dc["id"])
        floor = create_floor(client, headers, building["id"])
        room = create_room(client, headers, floor["id"])
        rack = create_rack(
            client, headers, room["id"],
            overrides={"height_units": 10},
        )
        return dc, building, floor, room, rack

    def test_check_placement_available(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/check-placement",
            json={
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fits"] is True
        assert data["reason"] == "Placement is available"

    def test_check_placement_overlap(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Existing",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/check-placement",
            json={
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fits"] is False
        assert len(data["overlapping_devices"]) == 1

    def test_check_placement_exceeds_rack(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/check-placement",
            json={
                "rack_unit_start": 9,
                "rack_unit_height": 3,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fits"] is False
        assert "exceed" in data["reason"].lower()

    def test_check_placement_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/racks/{fake_id}/check-placement",
            json={
                "rack_unit_start": 1,
                "rack_unit_height": 1,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_check_placement_exclude_device(
        self, client, owner_headers
    ):
        dc, building, floor, room, rack = self._setup_rack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack["id"],
            overrides={
                "name": "Existing",
                "rack_unit_start": 1,
                "rack_unit_height": 2,
            },
        )
        resp = client.post(
            f"/api/v1/racks/{rack['id']}/check-placement",
            json={
                "rack_unit_start": 1,
                "rack_unit_height": 2,
                "device_id": device["id"],
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fits"] is True
