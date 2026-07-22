from abc import ABC, abstractmethod
from datetime import datetime


class BaseBackgroundJob(ABC):
    @abstractmethod
    def run(self) -> dict:
        pass

    @property
    @abstractmethod
    def job_name(self) -> str:
        pass


class AlertEvaluationJob(BaseBackgroundJob):
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    @property
    def job_name(self) -> str:
        return "alert_evaluation"

    def run(self) -> dict:
        from app.services.alerting import (
            AlertingService,
        )

        db = self.db_session_factory()
        try:
            service = AlertingService(db)
            results = service.evaluate_all_rules()
            db.commit()
            return {
                "job": self.job_name,
                "executed_at": (
                    datetime.utcnow().isoformat()
                ),
                "results": results,
            }
        except Exception as e:
            db.rollback()
            return {
                "job": self.job_name,
                "executed_at": (
                    datetime.utcnow().isoformat()
                ),
                "error": str(e),
            }
        finally:
            db.close()


class IncidentCreationJob(BaseBackgroundJob):
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    @property
    def job_name(self) -> str:
        return "incident_creation"

    def run(self) -> dict:
        from app.services.alerting import (
            AlertingService,
        )

        db = self.db_session_factory()
        try:
            service = AlertingService(db)
            results = (
                service.create_incidents_for_critical_alerts()
            )
            db.commit()
            return {
                "job": self.job_name,
                "executed_at": (
                    datetime.utcnow().isoformat()
                ),
                "results": results,
            }
        except Exception as e:
            db.rollback()
            return {
                "job": self.job_name,
                "executed_at": (
                    datetime.utcnow().isoformat()
                ),
                "error": str(e),
            }
        finally:
            db.close()


class MaintenanceWindowCheckJob(BaseBackgroundJob):
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    @property
    def job_name(self) -> str:
        return "maintenance_window_check"

    def run(self) -> dict:
        from app.services.alerting import (
            AlertingService,
        )

        db = self.db_session_factory()
        try:
            service = AlertingService(db)
            results = (
                service.activate_scheduled_windows()
            )
            db.commit()
            return {
                "job": self.job_name,
                "executed_at": (
                    datetime.utcnow().isoformat()
                ),
                "results": results,
            }
        except Exception as e:
            db.rollback()
            return {
                "job": self.job_name,
                "executed_at": (
                    datetime.utcnow().isoformat()
                ),
                "error": str(e),
            }
        finally:
            db.close()


class BackgroundJobScheduler:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self._jobs = {}

    def register_job(
        self, job: BaseBackgroundJob
    ) -> None:
        self._jobs[job.job_name] = job

    def run_job(self, job_name: str) -> dict:
        job = self._jobs.get(job_name)
        if not job:
            return {
                "error": f"Job '{job_name}' not found"
            }
        return job.run()

    def run_all(self) -> list[dict]:
        results = []
        for job in self._jobs.values():
            results.append(job.run())
        return results

    def list_jobs(self) -> list[str]:
        return list(self._jobs.keys())
