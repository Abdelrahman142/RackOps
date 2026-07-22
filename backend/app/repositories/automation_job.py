import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.automation_job import AutomationJob


class AutomationJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        name: str,
        job_type: str,
        created_by: uuid.UUID,
        description: str | None = None,
    ) -> AutomationJob:
        job = AutomationJob(
            company_id=company_id,
            name=name,
            job_type=job_type,
            status="PENDING",
            created_by=created_by,
            description=description,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def get_by_id(
        self,
        company_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> AutomationJob | None:
        return (
            self.db.query(AutomationJob)
            .filter(
                AutomationJob.id == job_id,
                AutomationJob.company_id == company_id,
            )
            .first()
        )

    def list_jobs(
        self,
        company_id: uuid.UUID,
        job_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AutomationJob], int]:
        query = (
            self.db.query(AutomationJob)
            .filter(
                AutomationJob.company_id == company_id,
            )
        )
        if job_type:
            query = query.filter(
                AutomationJob.job_type == job_type
            )
        if status:
            query = query.filter(
                AutomationJob.status == status
            )

        total = query.count()
        items = (
            query.order_by(AutomationJob.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total

    def update_status(
        self,
        job: AutomationJob,
        status: str,
    ) -> AutomationJob:
        job.status = status
        if status == "RUNNING" and job.started_at is None:
            job.started_at = datetime.utcnow()
        elif status in ("SUCCESS", "FAILED", "CANCELLED"):
            job.completed_at = datetime.utcnow()
        self.db.flush()
        return job
