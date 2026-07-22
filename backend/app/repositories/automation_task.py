import uuid

from sqlalchemy.orm import Session

from app.models.automation_task import AutomationTask


class AutomationTaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        job_id: uuid.UUID,
        device_id: uuid.UUID,
        company_id: uuid.UUID,
        command: str,
        parameters: str | None = None,
    ) -> AutomationTask:
        task = AutomationTask(
            job_id=job_id,
            device_id=device_id,
            company_id=company_id,
            command=command,
            parameters=parameters,
            status="PENDING",
        )
        self.db.add(task)
        self.db.flush()
        return task

    def get_by_id(
        self,
        company_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> AutomationTask | None:
        return (
            self.db.query(AutomationTask)
            .filter(
                AutomationTask.id == task_id,
                AutomationTask.company_id == company_id,
            )
            .first()
        )

    def list_by_job(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> list[AutomationTask]:
        return (
            self.db.query(AutomationTask)
            .filter(
                AutomationTask.job_id == job_id,
                AutomationTask.company_id == company_id,
            )
            .order_by(AutomationTask.created_at)
            .all()
        )

    def update_status(
        self,
        task: AutomationTask,
        status: str,
        output: str | None = None,
        error_message: str | None = None,
    ) -> AutomationTask:
        from datetime import datetime

        task.status = status
        if status == "RUNNING":
            task.started_at = datetime.utcnow()
        elif status in ("SUCCESS", "FAILED"):
            task.completed_at = datetime.utcnow()
        if output is not None:
            task.output = output
        if error_message is not None:
            task.error_message = error_message
        self.db.flush()
        return task
