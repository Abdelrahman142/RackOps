from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class WorkerTask:
    task_id: UUID
    job_id: UUID
    company_id: UUID
    device_id: UUID
    command: str
    parameters: str | None = None
    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass
class WorkerResult:
    task_id: UUID
    success: bool
    output: str = ""
    error_message: str | None = None
    completed_at: datetime = field(
        default_factory=datetime.utcnow
    )


class BaseWorker(ABC):
    @abstractmethod
    def submit_task(self, task: WorkerTask) -> str:
        """Submit a task for async execution. Returns task reference."""
        pass

    @abstractmethod
    def get_task_status(self, reference: str) -> str:
        """Get the status of a submitted task."""
        pass

    @abstractmethod
    def cancel_task(self, reference: str) -> bool:
        """Cancel a running task."""
        pass

    @abstractmethod
    def get_queue_size(self) -> int:
        """Get the number of pending tasks."""
        pass


class InlineWorker(BaseWorker):
    def __init__(self):
        self._tasks: dict[str, WorkerTask] = {}
        self._results: dict[str, WorkerResult] = {}

    def submit_task(self, task: WorkerTask) -> str:
        ref = f"inline-{task.task_id}"
        self._tasks[ref] = task
        return ref

    def get_task_status(self, reference: str) -> str:
        if reference in self._results:
            result = self._results[reference]
            return "SUCCESS" if result.success else "FAILED"
        if reference in self._tasks:
            return "RUNNING"
        return "UNKNOWN"

    def cancel_task(self, reference: str) -> bool:
        self._tasks.pop(reference, None)
        return True

    def get_queue_size(self) -> int:
        return len(self._tasks)


class CeleryWorker(BaseWorker):
    def __init__(self, broker_url: str = "redis://localhost:6379/0"):
        self.broker_url = broker_url

    def submit_task(self, task: WorkerTask) -> str:
        try:
            from app.workers.celery_app import execute_automation_task

            result = execute_automation_task.delay(
                task_id=str(task.task_id),
                job_id=str(task.job_id),
                company_id=str(task.company_id),
                device_id=str(task.device_id),
                command=task.command,
                parameters=task.parameters,
            )
            return result.id
        except ImportError:
            raise RuntimeError("Celery is not configured")

    def get_task_status(self, reference: str) -> str:
        try:
            from app.workers.celery_app import celery_app

            result = celery_app.AsyncResult(reference)
            status_map = {
                "PENDING": "PENDING",
                "STARTED": "RUNNING",
                "SUCCESS": "SUCCESS",
                "FAILURE": "FAILED",
                "REVOKED": "CANCELLED",
            }
            return status_map.get(result.state, "UNKNOWN")
        except Exception:
            return "UNKNOWN"

    def cancel_task(self, reference: str) -> bool:
        try:
            from app.workers.celery_app import celery_app

            celery_app.control.revoke(reference, terminate=True)
            return True
        except Exception:
            return False

    def get_queue_size(self) -> int:
        try:
            from app.workers.celery_app import celery_app

            inspector = celery_app.control.inspect()
            reserved = inspector.reserved() or {}
            return sum(
                len(tasks) for tasks in reserved.values()
            )
        except Exception:
            return 0


def create_worker(
    worker_type: str = "inline", **kwargs
) -> BaseWorker:
    if worker_type == "celery":
        return CeleryWorker(**kwargs)
    return InlineWorker()
