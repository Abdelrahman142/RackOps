import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.engine.automation_engine import AutomationEngine
from app.models.automation_job import AutomationJob
from app.repositories.automation_job import (
    AutomationJobRepository,
)
from app.repositories.automation_task import (
    AutomationTaskRepository,
)
from app.utils.exceptions import (
    NotFoundException,
    ValidationException,
)

VALID_JOB_TYPES = {
    "COMMAND",
    "CONFIGURATION",
    "BACKUP",
    "DEPLOYMENT",
    "MAINTENANCE",
}

VALID_JOB_STATUSES = {
    "PENDING",
    "RUNNING",
    "SUCCESS",
    "FAILED",
    "CANCELLED",
}


class AutomationService:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = AutomationJobRepository(db)
        self.task_repo = AutomationTaskRepository(db)
        self.engine = AutomationEngine(db)

    def create_job(
        self,
        company_id: uuid.UUID,
        name: str,
        job_type: str,
        created_by: uuid.UUID,
        description: str | None = None,
    ) -> dict:
        if job_type not in VALID_JOB_TYPES:
            raise ValidationException(
                detail=f"Invalid job type: {job_type}. Valid types: {', '.join(VALID_JOB_TYPES)}"
            )
        self.db.commit()
        job = self.job_repo.create(
            company_id=company_id,
            name=name,
            job_type=job_type,
            created_by=created_by,
            description=description,
        )
        self.db.commit()
        self.db.refresh(job)
        return self._serialize_job(job)

    def get_job(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> dict:
        job = self.job_repo.get_by_id(company_id, job_id)
        if job is None:
            raise NotFoundException(
                detail="Automation job not found"
            )
        return self._serialize_job(job)

    def get_job_raw(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> AutomationJob:
        job = self.job_repo.get_by_id(company_id, job_id)
        if job is None:
            raise NotFoundException(
                detail="Automation job not found"
            )
        return job

    def list_jobs(
        self,
        company_id: uuid.UUID,
        job_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict], int]:
        items, total = self.job_repo.list_jobs(
            company_id, job_type, status, page, size
        )
        return [self._serialize_job(j) for j in items], total

    def execute_job(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> dict:
        job = self.get_job_raw(company_id, job_id)
        result = self.engine.execute_job(job)
        self.db.commit()
        self.db.refresh(result)
        return self._serialize_job(result)

    def cancel_job(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> dict:
        job = self.get_job_raw(company_id, job_id)
        result = self.engine.cancel_job(job)
        self.db.commit()
        self.db.refresh(result)
        return self._serialize_job(result)

    def create_task_for_job(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
        device_id: uuid.UUID,
        command: str,
        parameters: str | None = None,
    ):
        job = self.get_job_raw(company_id, job_id)
        if job.status != "PENDING":
            raise ValidationException(
                detail="Can only add tasks to PENDING jobs"
            )
        task = self.task_repo.create(
            job_id=job.id,
            device_id=device_id,
            company_id=company_id,
            command=command,
            parameters=parameters,
        )
        self.db.commit()
        return task

    def list_tasks(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> list[dict]:
        self.get_job_raw(company_id, job_id)
        tasks = self.task_repo.list_by_job(company_id, job_id)
        return [self._serialize_task(t) for t in tasks]

    def _serialize_job(self, job) -> dict:
        return {
            "id": str(job.id),
            "company_id": str(job.company_id),
            "name": job.name,
            "description": job.description,
            "job_type": job.job_type,
            "status": job.status,
            "created_by": str(job.created_by),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }

    def _serialize_task(self, task) -> dict:
        return {
            "id": str(task.id),
            "job_id": str(task.job_id),
            "device_id": str(task.device_id),
            "company_id": str(task.company_id),
            "command": task.command,
            "parameters": task.parameters,
            "status": task.status,
            "output": task.output,
            "error_message": task.error_message,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "created_at": task.created_at.isoformat(),
        }
