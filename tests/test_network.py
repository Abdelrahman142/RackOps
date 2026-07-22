import uuid

import pytest
from tests.conftest import (
    create_building,
    create_connection,
    create_device,
    create_floor,
    create_interface,
    create_ip,
    create_rack,
    create_room,
    create_subnet,
    create_vlan,
)


# ===========================
# Helpers
# ===========================


def _create_full_dc_stack(client, headers):
    dc = create_dc(client, headers)
    dc_id = dc["id"]
    building = create_building(client, headers, dc_id)
    building_id = building["id"]
    floor = create_floor(client, headers, building_id)
    floor_id = floor["id"]
    room = create_room(client, headers, floor_id)
    room_id = room["id"]
    rack = create_rack(client, headers, room_id)
    rack_id = rack["id"]
    return dc_id, building_id, floor_id, room_id, rack_id


def create_dc(client, headers, overrides=None):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"DC-{uid}",
        "code": f"DC{uid[:4].upper()}",
        "country": "US",
        "city": "Dallas",
        "address": "456 Server St",
        "timezone": "America/Chicago",
        "status": "ACTIVE",
    }
    if overrides:
        payload.update(overrides)
    resp = client.post(
        "/api/v1/datacenters",
        json=payload,
        headers=headers,
    )
    return resp.json()


def _setup_two_devices(client, headers):
    dc_id, _, _, _, rack_id = _create_full_dc_stack(
        client, headers
    )
    dev1 = create_device(client, headers, rack_id)
    dev2 = create_device(client, headers, rack_id)
    return dc_id, dev1["id"], dev2["id"]


# ===========================
# Interface CRUD Tests
# ===========================


class TestInterfaceCRUD:
    def test_create_interface(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        iface = create_interface(
            client, owner_headers, device["id"]
        )
        assert iface["id"]
        assert iface["device_id"] == device["id"]
        assert iface["interface_type"] == "ETHERNET"
        assert iface["status"] == "UP"

    def test_create_interface_with_fc_type(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            f"/api/v1/devices/{device['id']}/interfaces",
            json={
                "name": f"fc0/0-{uid}",
                "interface_type": "FIBRE_CHANNEL",
                "status": "UP",
                "speed_mbps": 32000,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["interface_type"] == "FIBRE_CHANNEL"
        assert data["speed_mbps"] == 32000

    def test_list_interfaces(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        create_interface(
            client, owner_headers, device["id"]
        )
        create_interface(
            client,
            owner_headers,
            device["id"],
            overrides={"name": "eth1-test"},
        )
        resp = client.get(
            f"/api/v1/devices/{device['id']}/interfaces",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    def test_get_interface(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        iface = create_interface(
            client, owner_headers, device["id"]
        )
        resp = client.get(
            f"/api/v1/interfaces/{iface['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == iface["id"]

    def test_get_nonexistent_interface(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/interfaces/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_update_interface(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        iface = create_interface(
            client, owner_headers, device["id"]
        )
        resp = client.patch(
            f"/api/v1/interfaces/{iface['id']}",
            json={
                "name": "eth0-renamed",
                "speed_mbps": 25000,
                "description": "Updated",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "eth0-renamed"
        assert resp.json()["speed_mbps"] == 25000

    def test_delete_interface(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        iface = create_interface(
            client, owner_headers, device["id"]
        )
        resp = client.delete(
            f"/api/v1/interfaces/{iface['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

        resp2 = client.get(
            f"/api/v1/interfaces/{iface['id']}",
            headers=owner_headers,
        )
        assert resp2.status_code == 404

    def test_duplicate_interface_name(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        create_interface(
            client, owner_headers, device["id"]
        )
        name = client.get(
            f"/api/v1/devices/{device['id']}/interfaces",
            headers=owner_headers,
        ).json()["interfaces"][0]["name"]
        resp = client.post(
            f"/api/v1/devices/{device['id']}/interfaces",
            json={
                "name": name,
                "interface_type": "ETHERNET",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_duplicate_mac_address(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        mac = "AA:BB:CC:DD:EE:01"
        create_interface(
            client,
            owner_headers,
            device["id"],
            overrides={"mac_address": mac},
        )
        device2 = create_device(
            client, owner_headers, rack_id
        )
        resp = client.post(
            f"/api/v1/devices/{device2['id']}/interfaces",
            json={
                "name": "eth0-dup",
                "mac_address": mac,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409


# ===========================
# Connection CRUD Tests
# ===========================


class TestConnectionCRUD:
    def test_create_connection(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        conn = create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        assert conn["id"]
        assert conn["connection_type"] == "COPPER"
        assert conn["status"] == "ACTIVE"

    def test_create_fiber_connection(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        resp = client.post(
            "/api/v1/connections",
            json={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
                "connection_type": "FIBER",
                "cable_type": "OM4",
                "length_meters": 15,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["connection_type"] == "FIBER"
        assert resp.json()["cable_type"] == "OM4"

    def test_list_connections(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        resp = client.get(
            "/api/v1/connections",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_connection(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        conn = create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        resp = client.get(
            f"/api/v1/connections/{conn['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_update_connection(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        conn = create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        resp = client.patch(
            f"/api/v1/connections/{conn['id']}",
            json={"status": "INACTIVE"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "INACTIVE"

    def test_delete_connection(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        conn = create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        resp = client.delete(
            f"/api/v1/connections/{conn['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_same_device_connection_rejected(
        self, client, owner_headers
    ):
        _, dev1_id, _ = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client,
            owner_headers,
            dev1_id,
            overrides={"name": "eth1-test"},
        )
        resp = client.post(
            "/api/v1/connections",
            json={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_duplicate_connection_rejected(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        resp = client.post(
            "/api/v1/connections",
            json={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409


# ===========================
# VLAN CRUD Tests
# ===========================


class TestVLANCRUD:
    def test_create_vlan(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        assert vlan["id"]
        assert vlan["vlan_id"] > 0

    def test_list_vlans(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        create_vlan(client, owner_headers, dc_id)
        create_vlan(client, owner_headers, dc_id)
        resp = client.get(
            f"/api/v1/datacenters/{dc_id}/vlans",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_get_vlan(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        resp = client.get(
            f"/api/v1/vlans/{vlan['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == vlan["id"]

    def test_update_vlan(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        resp = client.patch(
            f"/api/v1/vlans/{vlan['id']}",
            json={"name": "Renamed-VLAN"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed-VLAN"

    def test_delete_vlan(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        resp = client.delete(
            f"/api/v1/vlans/{vlan['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_duplicate_vlan_id_rejected(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        create_vlan(
            client,
            owner_headers,
            dc_id,
            overrides={"vlan_id": 100},
        )
        resp = client.post(
            f"/api/v1/datacenters/{dc_id}/vlans",
            json={
                "name": "Dup VLAN",
                "vlan_id": 100,
                "status": "ACTIVE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409

    def test_duplicate_vlan_name_rejected(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        create_vlan(
            client,
            owner_headers,
            dc_id,
            overrides={"name": "SameName"},
        )
        resp = client.post(
            f"/api/v1/datacenters/{dc_id}/vlans",
            json={
                "name": "SameName",
                "vlan_id": 200,
                "status": "ACTIVE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409


# ===========================
# Subnet CRUD Tests
# ===========================


class TestSubnetCRUD:
    def test_create_subnet(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        assert subnet["id"]
        assert subnet["cidr"] == 24

    def test_list_subnets(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        create_subnet(
            client, owner_headers, vlan["id"]
        )
        create_subnet(
            client,
            owner_headers,
            vlan["id"],
            overrides={
                "network_address": "10.2.0.0",
                "cidr": 16,
            },
        )
        resp = client.get(
            f"/api/v1/vlans/{vlan['id']}/subnets",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_get_subnet(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        resp = client.get(
            f"/api/v1/subnets/{subnet['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_update_subnet(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        resp = client.patch(
            f"/api/v1/subnets/{subnet['id']}",
            json={"gateway": "10.1.0.254"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["gateway"] == "10.1.0.254"

    def test_delete_subnet(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        resp = client.delete(
            f"/api/v1/subnets/{subnet['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_duplicate_subnet_rejected(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        create_subnet(
            client,
            owner_headers,
            vlan["id"],
            overrides={
                "network_address": "10.99.0.0",
                "cidr": 24,
            },
        )
        resp = client.post(
            f"/api/v1/vlans/{vlan['id']}/subnets",
            json={
                "network_address": "10.99.0.0",
                "cidr": 24,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409


# ===========================
# IP Address CRUD Tests
# ===========================


class TestIPAddressCRUD:
    def test_create_ip(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        ip = create_ip(
            client, owner_headers, subnet["id"]
        )
        assert ip["id"]
        assert ip["status"] == "AVAILABLE"

    def test_create_ip_with_interface(
        self, client, owner_headers
    ):
        dc_id, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        iface = create_interface(
            client, owner_headers, device["id"]
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        ip = create_ip(
            client,
            owner_headers,
            subnet["id"],
            overrides={
                "device_interface_id": iface["id"],
                "status": "AVAILABLE",
            },
        )
        assert ip["device_interface_id"] == iface["id"]
        assert ip["status"] == "ASSIGNED"

    def test_list_ips(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        create_ip(
            client, owner_headers, subnet["id"]
        )
        create_ip(
            client,
            owner_headers,
            subnet["id"],
            overrides={"address": "10.10.1.10"},
        )
        resp = client.get(
            f"/api/v1/subnets/{subnet['id']}/ips",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_get_ip(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        ip = create_ip(
            client, owner_headers, subnet["id"]
        )
        resp = client.get(
            f"/api/v1/ips/{ip['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_update_ip(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        ip = create_ip(
            client, owner_headers, subnet["id"]
        )
        resp = client.patch(
            f"/api/v1/ips/{ip['id']}",
            json={"status": "RESERVED"},
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESERVED"

    def test_delete_ip(self, client, owner_headers):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        ip = create_ip(
            client, owner_headers, subnet["id"]
        )
        resp = client.delete(
            f"/api/v1/ips/{ip['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200

    def test_duplicate_ip_rejected(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        create_ip(
            client,
            owner_headers,
            subnet["id"],
            overrides={"address": "10.88.1.1"},
        )
        resp = client.post(
            f"/api/v1/subnets/{subnet['id']}/ips",
            json={
                "address": "10.88.1.1",
                "status": "AVAILABLE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 409


# ===========================
# Network Map Tests
# ===========================


class TestNetworkMap:
    def test_get_empty_network_map(
        self, client, owner_headers
    ):
        resp = client.get(
            "/api/v1/network-map",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_nodes"] == 0
        assert data["total_edges"] == 0

    def test_network_map_with_connections(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        resp = client.get(
            "/api/v1/network-map",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_nodes"] == 2
        assert data["total_edges"] == 1
        node_ids = {n["node_id"] for n in data["nodes"]}
        assert dev1_id in node_ids
        assert dev2_id in node_ids


# ===========================
# RBAC Tests
# ===========================


class TestRBAC:
    def test_viewer_can_read_interfaces(
        self, client, owner_headers, viewer_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        create_interface(
            client, owner_headers, device["id"]
        )
        resp = client.get(
            f"/api/v1/devices/{device['id']}/interfaces",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_cannot_create_interface(
        self, client, owner_headers, viewer_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/interfaces",
            json={"name": "eth0"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_engineer_can_create_interface(
        self, client, owner_headers, engineer_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/interfaces",
            json={
                "name": "eth0",
                "interface_type": "ETHERNET",
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_engineer_can_create_connection(
        self, client, owner_headers, engineer_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        resp = client.post(
            "/api/v1/connections",
            json={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_viewer_can_read_connections(
        self, client, owner_headers, viewer_headers
    ):
        resp = client.get(
            "/api/v1/connections",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_cannot_create_vlan(
        self, client, owner_headers, viewer_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/datacenters/{dc_id}/vlans",
            json={"name": "VLAN1", "vlan_id": 1},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_can_read_vlans(
        self, client, owner_headers, viewer_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        resp = client.get(
            f"/api/v1/datacenters/{dc_id}/vlans",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_viewer_can_read_network_map(
        self, client, owner_headers, viewer_headers
    ):
        resp = client.get(
            "/api/v1/network-map",
            headers=viewer_headers,
        )
        assert resp.status_code == 200


# ===========================
# Interface Validation Tests
# ===========================


class TestInterfaceValidation:
    def test_invalid_interface_type(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/interfaces",
            json={
                "name": "bad0",
                "interface_type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_invalid_status(
        self, client, owner_headers
    ):
        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/interfaces",
            json={
                "name": "bad0",
                "status": "BROKEN",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_delete_interface_with_connection(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        create_connection(
            client,
            owner_headers,
            overrides={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
            },
        )
        resp = client.delete(
            f"/api/v1/interfaces/{iface1['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ===========================
# VLAN Validation Tests
# ===========================


class TestVLANValidation:
    def test_invalid_vlan_status(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/datacenters/{dc_id}/vlans",
            json={
                "name": "Bad",
                "vlan_id": 1,
                "status": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_vlan_id_out_of_range(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        resp = client.post(
            f"/api/v1/datacenters/{dc_id}/vlans",
            json={
                "name": "Bad",
                "vlan_id": 5000,
                "status": "ACTIVE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ===========================
# Connection Validation Tests
# ===========================


class TestConnectionValidation:
    def test_same_interface_connection(
        self, client, owner_headers
    ):
        _, dev1_id, _ = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        resp = client.post(
            "/api/v1/connections",
            json={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface1["id"],
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_invalid_connection_type(
        self, client, owner_headers
    ):
        _, dev1_id, dev2_id = _setup_two_devices(
            client, owner_headers
        )
        iface1 = create_interface(
            client, owner_headers, dev1_id
        )
        iface2 = create_interface(
            client, owner_headers, dev2_id
        )
        resp = client.post(
            "/api/v1/connections",
            json={
                "source_interface_id": iface1["id"],
                "destination_interface_id": iface2["id"],
                "connection_type": "WIRELESS",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ===========================
# IP Validation Tests
# ===========================


class TestIPValidation:
    def test_invalid_ip_status(
        self, client, owner_headers
    ):
        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )
        subnet = create_subnet(
            client, owner_headers, vlan["id"]
        )
        resp = client.post(
            f"/api/v1/subnets/{subnet['id']}/ips",
            json={
                "address": "10.10.1.1",
                "status": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ===========================
# Tenant Isolation Tests
# ===========================


class TestTenantIsolation:
    def test_cross_company_interface_access(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
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

        _, _, _, _, rack_id = _create_full_dc_stack(
            client, owner_headers
        )
        device = create_device(
            client, owner_headers, rack_id
        )
        iface = create_interface(
            client, owner_headers, device["id"]
        )

        resp = client.get(
            f"/api/v1/interfaces/{iface['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404

    def test_cross_company_vlan_access(
        self, client, owner_headers
    ):
        uid = uuid.uuid4().hex[:8]
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"OtherCo2-{uid}",
                "company_email": f"other2-{uid}@test.com",
                "name": "Other2",
                "email": f"other2-{uid}@test.com",
                "password": "testpass123",
                "country": "US",
            },
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"other2-{uid}@test.com",
                "password": "testpass123",
            },
        )
        other_headers = {
            "Authorization": (
                f"Bearer {other_login.json()['access_token']}"
            )
        }

        dc_id, _, _, _, _ = _create_full_dc_stack(
            client, owner_headers
        )
        vlan = create_vlan(
            client, owner_headers, dc_id
        )

        resp = client.get(
            f"/api/v1/vlans/{vlan['id']}",
            headers=other_headers,
        )
        assert resp.status_code == 404
