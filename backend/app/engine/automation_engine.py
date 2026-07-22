from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.connectors import create_connector
from app.connectors.base import ConnectorResult
from app.models.automation_job import AutomationJob
from app.models.automation_task import AutomationTask
from app.models.device_connector import DeviceConnector
from app.repositories.automation_job import (
    AutomationJobRepository,
)
from app.repositories.automation_task import (
    AutomationTaskRepository,
)
from app.repositories.device_connector import (
    DeviceConnectorRepository,
)
from app.utils.exceptions import ValidationException


class AutomationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = AutomationJobRepository(db)
        self.task_repo = AutomationTaskRepository(db)
        self.connector_repo = DeviceConnectorRepository(db)

    def execute_job(self, job: AutomationJob) -> AutomationJob:
        if job.status != "PENDING":
            raise ValidationException(
                detail=f"Job is not in PENDING status (current: {job.status})"
            )

        self.job_repo.update_status(job, "RUNNING")

        tasks = self.task_repo.list_by_job(
            job.company_id, job.id
        )
        all_success = True

        for task in tasks:
            self._execute_task(task)
            if task.status == "FAILED":
                all_success = False

        final_status = "SUCCESS" if all_success else "FAILED"
        self.job_repo.update_status(job, final_status)
        return job

    def _execute_task(self, task: AutomationTask) -> None:
        self.task_repo.update_status(task, "RUNNING")

        connector = self.connector_repo.get_by_id(
            task.company_id, task.device_id
        )
        if connector is None:
            self.task_repo.update_status(
                task,
                "FAILED",
                error_message="No connector found for device",
            )
            return

        if not connector.enabled:
            self.task_repo.update_status(
                task,
                "FAILED",
                error_message="Connector is disabled",
            )
            return

        try:
            conn = create_connector(
                connector_type=connector.connector_type,
                hostname=connector.hostname,
                port=connector.port,
                username=connector.username,
                password=connector.encrypted_password,
            )

            connect_result = conn.connect()
            if not connect_result.success:
                self.task_repo.update_status(
                    task,
                    "FAILED",
                    error_message=f"Connection failed: {connect_result.error_message}",
                )
                return

            exec_result = conn.execute(
                command=task.command,
                parameters=task.parameters,
            )

            conn.disconnect()

            if exec_result.success:
                self.task_repo.update_status(
                    task,
                    "SUCCESS",
                    output=exec_result.output,
                )
            else:
                self.task_repo.update_status(
                    task,
                    "FAILED",
                    output=exec_result.output,
                    error_message=exec_result.error_message,
                )
        except Exception as e:
            self.task_repo.update_status(
                task,
                "FAILED",
                error_message=str(e),
            )

    def cancel_job(self, job: AutomationJob) -> AutomationJob:
        if job.status not in ("PENDING", "RUNNING"):
            raise ValidationException(
                detail=f"Cannot cancel job in status: {job.status}"
            )

        self.job_repo.update_status(job, "CANCELLED")

        tasks = self.task_repo.list_by_job(
            job.company_id, job.id
        )
        for task in tasks:
            if task.status in ("PENDING",):
                self.task_repo.update_status(
                    task, "CANCELLED"
                )

        return job

    def test_connector(
        self, connector: DeviceConnector
    ) -> ConnectorResult:
        try:
            conn = create_connector(
                connector_type=connector.connector_type,
                hostname=connector.hostname,
                port=connector.port,
                username=connector.username,
                password=connector.encrypted_password,
            )
            result = conn.test_connection()
            self.connector_repo.update_last_connection_test(
                connector, datetime.utcnow()
            )
            return result
        except Exception as e:
            return ConnectorResult(
                success=False,
                output="",
                error_message=str(e),
            )
