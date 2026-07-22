import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.collectors.registry import get_collector
from app.repositories.health_check import (
    HealthCheckRepository,
)
from app.repositories.metric_data import (
    MetricDataRepository,
)
from app.repositories.metric_definition import (
    MetricDefinitionRepository,
)
from app.repositories.monitoring_target import (
    MonitoringTargetRepository,
)


class MetricCollectionScheduler:
    def __init__(self, db: Session):
        self.db = db
        self.target_repo = MonitoringTargetRepository(db)
        self.definition_repo = MetricDefinitionRepository(
            db
        )
        self.metric_repo = MetricDataRepository(db)
        self.health_repo = HealthCheckRepository(db)

    def collect_for_target(
        self,
        company_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> dict:
        target = (
            self.target_repo.get_active_by_company_and_id(
                company_id, target_id
            )
        )

        if not target:
            return {
                "status": "error",
                "message": "Target not found",
            }

        if not target.enabled:
            return {
                "status": "skipped",
                "message": "Target is disabled",
            }

        collector = get_collector(target.collector_type)

        if not collector:
            return {
                "status": "error",
                "message": (
                    f"No collector for "
                    f"{target.collector_type}"
                ),
            }

        now = datetime.utcnow()

        health_status = collector.check_health(
            target.endpoint, target.port
        )

        self.health_repo.create(
            company_id=company_id,
            device_id=target.device_id,
            status=health_status.status,
            response_time_ms=health_status.response_time_ms,
            checked_at=now,
        )

        metrics_stored = 0

        if health_status.status == "UP":
            collected = collector.collect(
                target.endpoint,
                target.port,
                collector.supported_metrics,
            )

            for cm in collected:
                defn = (
                    self.definition_repo.get_by_metric_key(
                        cm.metric_key
                    )
                )

                if not defn:
                    defn = self.definition_repo.create(
                        name=cm.metric_key.replace(
                            "_", " "
                        ).title(),
                        metric_key=cm.metric_key,
                        unit=cm.unit,
                        category=self._categorize(
                            cm.metric_key
                        ),
                    )
                    self.db.flush()

                self.metric_repo.create(
                    company_id=company_id,
                    device_id=target.device_id,
                    target_id=target.id,
                    metric_definition_id=defn.id,
                    value=cm.value,
                    timestamp=now,
                )
                metrics_stored += 1

        self.target_repo.update(
            target,
            status=health_status.status,
            last_check_at=now,
        )

        self.db.commit()

        return {
            "status": "completed",
            "health": health_status.status,
            "metrics_stored": metrics_stored,
            "response_time_ms": (
                health_status.response_time_ms
            ),
        }

    def collect_all_enabled(
        self,
        company_id: uuid.UUID,
    ) -> list[dict]:
        targets = (
            self.target_repo.list_enabled_by_company(
                company_id
            )
        )

        results = []
        for target in targets:
            result = self.collect_for_target(
                company_id, target.id
            )
            results.append({
                "target_id": str(target.id),
                "device_id": str(target.device_id),
                **result,
            })

        return results

    def _categorize(self, metric_key: str) -> str:
        if "cpu" in metric_key or "load" in metric_key:
            return "CPU"
        if (
            "memory" in metric_key
            or "swap" in metric_key
        ):
            return "MEMORY"
        if "disk" in metric_key:
            return "DISK"
        if (
            "network" in metric_key
            or "if_" in metric_key
        ):
            return "NETWORK"
        if "power" in metric_key:
            return "POWER"
        if "temperature" in metric_key:
            return "TEMPERATURE"
        return "OTHER"

    def cleanup_old_metrics(
        self,
        company_id: uuid.UUID,
        days: int = 90,
    ) -> dict:
        cutoff = datetime.utcnow()

        from datetime import timedelta

        cutoff = cutoff - timedelta(days=days)

        count = self.metric_repo.delete_old_data(
            company_id, cutoff
        )

        return {
            "deleted_count": count,
            "cutoff_date": cutoff.isoformat(),
        }
