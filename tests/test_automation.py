import uuid

import pytest

from tests.conftest import (
    create_backup,
    create_building,
    create_device,
    create_device_connector,
    create_floor,
    create_room,
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
    floor = create_floor(client, headers, building["id"])
    room = create_room(client, headers, floor["id"])
    return dc_id, building["id"], floor["id"], room["id"]


def _create_rack_and_device(client, headers, room_id):
    uid = uuid.uuid4().hex[:8]
    rack = client.post(
        f"/api/v1/rooms/{room_id}/racks",
        json={
            "name": f"Rack-{uid}",
            "code": f"RK{uid[:4].upper()}",
            "rack_type": "SERVER_RACK",
            "status": "ACTIVE",
            "height_units": 42,
        },
        headers=headers,
    ).json()
    device = create_device(client, headers, rack["id"])
    return rack, device


# ===========================
# Automation Job Tests
# ===========================


class TestAutomationJobs:
    def test_create_job(self, client, owner_headers):
        resp = client.post(
            "/api/v1/automation/jobs",
            json={
                "name": "Test Job",
                "job_type": "COMMAND",
                "description": "A test job",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Job"
        assert data["job_type"] == "COMMAND"
        assert data["status"] == "PENDING"

    def test_create_job_requires_auth(self, client):
        resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Test", "job_type": "COMMAND"},
        )
        assert resp.status_code in (401, 403)

    def test_create_job_invalid_type(self, client, owner_headers):
        resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Test", "job_type": "INVALID"},
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_jobs_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/automation/jobs",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["jobs"] == []
        assert data["total"] == 0

    def test_list_jobs_with_data(self, client, owner_headers):
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "Job 1", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "Job 2", "job_type": "BACKUP"},
            headers=owner_headers,
        )
        resp = client.get(
            "/api/v1/automation/jobs",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_list_jobs_filter_by_type(
        self, client, owner_headers
    ):
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "Cmd", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "Bak", "job_type": "BACKUP"},
            headers=owner_headers,
        )
        resp = client.get(
            "/api/v1/automation/jobs?job_type=BACKUP",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["jobs"][0]["job_type"] == "BACKUP"

    def test_list_jobs_filter_by_status(
        self, client, owner_headers
    ):
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "Job", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        resp = client.get(
            "/api/v1/automation/jobs?status=PENDING",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_job(self, client, owner_headers):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Get Me", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        job_id = create_resp.json()["id"]
        resp = client.get(
            f"/api/v1/automation/jobs/{job_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Me"

    def test_get_job_not_found(self, client, owner_headers):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/automation/jobs/{fake_id}",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_execute_job_empty(self, client, owner_headers):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Empty", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        job_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/automation/jobs/{job_id}/execute",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "SUCCESS"

    def test_execute_job_already_executed(
        self, client, owner_headers
    ):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Done", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        job_id = create_resp.json()["id"]
        client.post(
            f"/api/v1/automation/jobs/{job_id}/execute",
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/automation/jobs/{job_id}/execute",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_cancel_pending_job(self, client, owner_headers):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Cancel", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        job_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/automation/jobs/{job_id}/cancel",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_cancel_completed_job_fails(
        self, client, owner_headers
    ):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Done", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        job_id = create_resp.json()["id"]
        client.post(
            f"/api/v1/automation/jobs/{job_id}/execute",
            headers=owner_headers,
        )
        resp = client.post(
            f"/api/v1/automation/jobs/{job_id}/cancel",
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_tasks_for_job(self, client, owner_headers):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/automation/jobs/{fake_id}/tasks",
            headers=owner_headers,
        )
        assert resp.status_code == 404

    def test_execute_on_devices(self, client, owner_headers):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            "/api/v1/automation/execute",
            json={
                "device_ids": [device["id"]],
                "command": "uptime",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["job_type"] == "COMMAND"

    def test_job_isolation_between_companies(
        self, client, owner_headers
    ):
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "OwnerJob", "job_type": "COMMAND"},
            headers=owner_headers,
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
        resp = client.get(
            "/api/v1/automation/jobs",
            headers=other_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_pagination(self, client, owner_headers):
        for i in range(5):
            client.post(
                "/api/v1/automation/jobs",
                json={
                    "name": f"Job-{i}",
                    "job_type": "COMMAND",
                },
                headers=owner_headers,
            )
        resp = client.get(
            "/api/v1/automation/jobs?page=1&size=2",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["jobs"]) == 2
        assert data["pages"] == 3


# ===========================
# Device Connector Tests
# ===========================


class TestDeviceConnectors:
    def test_create_connector(self, client, owner_headers):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/connectors",
            json={
                "connector_type": "SSH",
                "hostname": "192.168.1.100",
                "port": 22,
                "username": "admin",
                "password": "secret123",
                "enabled": True,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["connector_type"] == "SSH"
        assert data["hostname"] == "192.168.1.100"
        assert data["enabled"] is True
        assert "password" not in data
        assert "encrypted_password" not in data

    def test_create_snmp_connector(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/connectors",
            json={
                "connector_type": "SNMP",
                "hostname": "192.168.1.100",
                "port": 161,
                "username": "snmp_user",
                "enabled": True,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["connector_type"] == "SNMP"

    def test_create_api_connector(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/connectors",
            json={
                "connector_type": "API",
                "hostname": "192.168.1.100",
                "port": 443,
                "username": "api_user",
                "enabled": True,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["connector_type"] == "API"

    def test_create_ansible_connector(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/connectors",
            json={
                "connector_type": "ANSIBLE",
                "hostname": "192.168.1.100",
                "port": 22,
                "username": "ansible",
                "enabled": True,
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["connector_type"] == "ANSIBLE"

    def test_create_invalid_connector_type(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/connectors",
            json={
                "connector_type": "INVALID",
                "hostname": "10.0.0.1",
                "username": "admin",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_connectors(self, client, owner_headers):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        create_device_connector(
            client, owner_headers, device["id"]
        )
        create_device_connector(
            client,
            owner_headers,
            device["id"],
            overrides={
                "connector_type": "SNMP",
                "port": 161,
                "hostname": "10.0.0.2",
            },
        )
        resp = client.get(
            f"/api/v1/devices/{device['id']}/connectors",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_connector_no_password_leak(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = create_device_connector(
            client, owner_headers, device["id"]
        )
        assert "password" not in resp
        assert "encrypted_password" not in resp

    def test_connector_requires_write_role(
        self, client, owner_headers, viewer_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/connectors",
            json={
                "connector_type": "SSH",
                "hostname": "10.0.0.1",
                "username": "admin",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403


# ===========================
# Backup Tests
# ===========================


class TestBackups:
    def test_create_backup(self, client, owner_headers):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/backups",
            json={
                "device_id": device["id"],
                "backup_type": "CONFIG",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["backup_type"] == "CONFIG"
        assert data["status"] == "COMPLETED"
        assert data["checksum"] is not None

    def test_create_full_backup(self, client, owner_headers):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/backups",
            json={
                "device_id": device["id"],
                "backup_type": "FULL",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["backup_type"] == "FULL"

    def test_create_database_backup(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/backups",
            json={
                "device_id": device["id"],
                "backup_type": "DATABASE",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["backup_type"] == "DATABASE"

    def test_invalid_backup_type(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/backups",
            json={
                "device_id": device["id"],
                "backup_type": "INVALID",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 422

    def test_list_backups(self, client, owner_headers):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        create_backup(client, owner_headers, device["id"])
        create_backup(
            client,
            owner_headers,
            device["id"],
            overrides={"backup_type": "FULL"},
        )
        resp = client.get(
            f"/api/v1/devices/{device['id']}/backups",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_backup_requires_write_role(
        self, client, owner_headers, viewer_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            f"/api/v1/devices/{device['id']}/backups",
            json={
                "device_id": device["id"],
                "backup_type": "CONFIG",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_backup_read_allowed_for_viewer(
        self, client, owner_headers, viewer_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.get(
            f"/api/v1/devices/{device['id']}/backups",
            headers=viewer_headers,
        )
        assert resp.status_code == 200


# ===========================
# Audit Log Tests
# ===========================


class TestAuditLogs:
    def test_audit_logs_empty(self, client, owner_headers):
        resp = client.get(
            "/api/v1/audit-logs",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["logs"] == []
        assert data["total"] == 0

    def test_audit_logs_after_job_creation(
        self, client, owner_headers
    ):
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "Audited", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        resp = client.get(
            "/api/v1/audit-logs",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        log = data["logs"][0]
        assert log["action"] == "CREATE"
        assert log["resource"] == "AUTOMATION_JOB"

    def test_audit_logs_filter_by_action(
        self, client, owner_headers
    ):
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "J1", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        resp = client.get(
            "/api/v1/audit-logs?action=CREATE",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_audit_logs_filter_by_resource(
        self, client, owner_headers
    ):
        client.post(
            "/api/v1/automation/jobs",
            json={"name": "J1", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        resp = client.get(
            "/api/v1/audit-logs?resource=AUTOMATION_JOB",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_audit_logs_after_connector_creation(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        create_device_connector(
            client, owner_headers, device["id"]
        )
        resp = client.get(
            "/api/v1/audit-logs?resource=DEVICE_CONNECTOR",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_audit_logs_after_backup(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        create_backup(client, owner_headers, device["id"])
        resp = client.get(
            "/api/v1/audit-logs?resource=CONFIGURATION_BACKUP",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_audit_logs_pagination(
        self, client, owner_headers
    ):
        for i in range(3):
            client.post(
                "/api/v1/automation/jobs",
                json={"name": f"J-{i}", "job_type": "COMMAND"},
                headers=owner_headers,
            )
        resp = client.get(
            "/api/v1/audit-logs?page=1&size=2",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3
        assert len(data["logs"]) == 2

    def test_audit_logs_requires_viewer(
        self, client, viewer_headers
    ):
        resp = client.get(
            "/api/v1/audit-logs",
            headers=viewer_headers,
        )
        assert resp.status_code == 200

    def test_audit_logs_requires_auth(self, client):
        resp = client.get("/api/v1/audit-logs")
        assert resp.status_code in (401, 403)


# ===========================
# RBAC Tests
# ===========================


class TestAutomationRBAC:
    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/automation/jobs",
            "/api/v1/audit-logs",
        ],
    )
    def test_read_endpoints_accept_viewer(
        self, client, viewer_headers, endpoint
    ):
        resp = client.get(endpoint, headers=viewer_headers)
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/automation/jobs",
            "/api/v1/audit-logs",
        ],
    )
    def test_read_endpoints_accept_admin(
        self, client, admin_headers, endpoint
    ):
        resp = client.get(endpoint, headers=admin_headers)
        assert resp.status_code == 200

    def test_viewer_cannot_create_job(
        self, client, viewer_headers
    ):
        resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Nope", "job_type": "COMMAND"},
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_execute_job(
        self, client, viewer_headers, owner_headers
    ):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Job", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        job_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/automation/jobs/{job_id}/execute",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_cancel_job(
        self, client, viewer_headers, owner_headers
    ):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "Job", "job_type": "COMMAND"},
            headers=owner_headers,
        )
        job_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/automation/jobs/{job_id}/cancel",
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_engineer_can_create_job(
        self, client, engineer_headers
    ):
        resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "EngJob", "job_type": "COMMAND"},
            headers=engineer_headers,
        )
        assert resp.status_code == 201

    def test_engineer_can_execute_job(
        self, client, engineer_headers
    ):
        create_resp = client.post(
            "/api/v1/automation/jobs",
            json={"name": "EngJob", "job_type": "COMMAND"},
            headers=engineer_headers,
        )
        job_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/automation/jobs/{job_id}/execute",
            headers=engineer_headers,
        )
        assert resp.status_code == 200


# ===========================
# Connector Test Endpoint
# ===========================


class TestConnectorTestEndpoint:
    def test_connector_not_reachable(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, device = _create_rack_and_device(
            client, owner_headers, room_id
        )
        connector = create_device_connector(
            client,
            owner_headers,
            device["id"],
            overrides={
                "hostname": "192.0.2.1",
            },
        )
        resp = client.post(
            f"/api/v1/connectors/{connector['id']}/test",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data
        assert "message" in data
        assert "tested_at" in data

    def test_connector_test_not_found(
        self, client, owner_headers
    ):
        fake_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/v1/connectors/{fake_id}/test",
            headers=owner_headers,
        )
        assert resp.status_code == 404


# ===========================
# Execute on Multiple Devices
# ===========================


class TestExecuteOnDevices:
    def test_execute_on_multiple_devices(
        self, client, owner_headers
    ):
        dc_id, _, _, room_id = _create_full_dc_stack(
            client, owner_headers
        )
        _, dev1 = _create_rack_and_device(
            client, owner_headers, room_id
        )
        _, dev2 = _create_rack_and_device(
            client, owner_headers, room_id
        )
        resp = client.post(
            "/api/v1/automation/execute",
            json={
                "device_ids": [dev1["id"], dev2["id"]],
                "command": "uptime",
            },
            headers=owner_headers,
        )
        assert resp.status_code == 201
        job = resp.json()
        assert job["job_type"] == "COMMAND"

        tasks_resp = client.get(
            f"/api/v1/automation/jobs/{job['id']}/tasks",
            headers=owner_headers,
        )
        assert tasks_resp.status_code == 200
        assert tasks_resp.json()["total"] == 2

    def test_execute_requires_at_least_one_device(
        self, client, owner_headers
    ):
        resp = client.post(
            "/api/v1/automation/execute",
            json={"device_ids": [], "command": "uptime"},
            headers=owner_headers,
        )
        assert resp.status_code == 422


# ===========================
# Connector Factory Tests
# ===========================


class TestConnectorFactory:
    def test_create_ssh_connector(self):
        from app.connectors import create_connector

        conn = create_connector(
            "SSH", "10.0.0.1", 22, "admin", "pass"
        )
        assert conn.__class__.__name__ == "SSHConnector"

    def test_create_snmp_connector(self):
        from app.connectors import create_connector

        conn = create_connector(
            "SNMP", "10.0.0.1", 161, "user"
        )
        assert conn.__class__.__name__ == "SNMPConnector"

    def test_create_api_connector(self):
        from app.connectors import create_connector

        conn = create_connector(
            "API", "10.0.0.1", 443, "user"
        )
        assert conn.__class__.__name__ == "APIConnector"

    def test_create_ansible_connector(self):
        from app.connectors import create_connector

        conn = create_connector(
            "ANSIBLE", "10.0.0.1", 22, "ansible"
        )
        assert (
            conn.__class__.__name__ == "AnsibleConnector"
        )

    def test_create_invalid_connector_raises(self):
        from app.connectors import create_connector

        with pytest.raises(ValueError):
            create_connector("INVALID", "10.0.0.1")

    def test_get_supported_types(self):
        from app.connectors import (
            get_supported_connector_types,
        )

        types = get_supported_connector_types()
        assert "SSH" in types
        assert "SNMP" in types
        assert "API" in types
        assert "ANSIBLE" in types

    def test_ssh_connector_connect_failure(self):
        from app.connectors import create_connector

        conn = create_connector(
            "SSH", "192.0.2.1", 22, "admin", "pass"
        )
        result = conn.connect()
        assert result.success is False
        assert result.error_message is not None

    def test_ssh_execute_not_connected(self):
        from app.connectors import create_connector

        conn = create_connector(
            "SSH", "10.0.0.1", 22, "admin", "pass"
        )
        result = conn.execute("uptime")
        assert result.success is False
        assert "Not connected" in result.error_message

    def test_ssh_disconnect(self):
        from app.connectors import create_connector

        conn = create_connector(
            "SSH", "10.0.0.1", 22, "admin", "pass"
        )
        result = conn.disconnect()
        assert result.success is True
        assert conn.is_connected is False

    def test_snmp_connector_connect_failure(self):
        from app.connectors import create_connector

        conn = create_connector(
            "SNMP", "192.0.2.1", 161, "user"
        )
        result = conn.connect()
        assert result.success is False

    def test_api_connector_connect_failure(self):
        from app.connectors import create_connector

        conn = create_connector(
            "API", "192.0.2.1", 443, "user"
        )
        result = conn.connect()
        assert result.success is False

    def test_connector_result_dataclass(self):
        from app.connectors.base import ConnectorResult
        from datetime import datetime

        r = ConnectorResult(
            success=True, output="ok"
        )
        assert r.success is True
        assert r.output == "ok"
        assert r.error_message is None
        assert isinstance(r.executed_at, datetime)


# ===========================
# Worker Tests
# ===========================


class TestWorkers:
    def test_inline_worker_submit(self):
        from app.workers import (
            InlineWorker,
            WorkerTask,
        )
        from uuid import uuid4

        worker = InlineWorker()
        task = WorkerTask(
            task_id=uuid4(),
            job_id=uuid4(),
            company_id=uuid4(),
            device_id=uuid4(),
            command="uptime",
        )
        ref = worker.submit_task(task)
        assert ref is not None
        assert worker.get_queue_size() == 1

    def test_inline_worker_status(self):
        from app.workers import (
            InlineWorker,
            WorkerTask,
        )
        from uuid import uuid4

        worker = InlineWorker()
        task = WorkerTask(
            task_id=uuid4(),
            job_id=uuid4(),
            company_id=uuid4(),
            device_id=uuid4(),
            command="uptime",
        )
        ref = worker.submit_task(task)
        assert worker.get_task_status(ref) == "RUNNING"
        assert worker.get_task_status("nonexistent") == "UNKNOWN"

    def test_inline_worker_cancel(self):
        from app.workers import (
            InlineWorker,
            WorkerTask,
        )
        from uuid import uuid4

        worker = InlineWorker()
        task = WorkerTask(
            task_id=uuid4(),
            job_id=uuid4(),
            company_id=uuid4(),
            device_id=uuid4(),
            command="uptime",
        )
        ref = worker.submit_task(task)
        assert worker.cancel_task(ref) is True
        assert worker.get_queue_size() == 0

    def test_create_inline_worker(self):
        from app.workers import create_worker

        worker = create_worker("inline")
        assert worker.__class__.__name__ == "InlineWorker"
