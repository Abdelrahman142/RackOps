from datetime import datetime

from app.collectors.base import (
    BaseCollector,
    CollectedMetric,
    HealthStatus,
)


class AgentCollector(BaseCollector):
    @property
    def collector_type(self) -> str:
        return "AGENT"

    @property
    def supported_metrics(self) -> list[str]:
        return [
            "cpu_usage_percent",
            "memory_usage_percent",
            "disk_usage_percent",
            "network_bytes_in",
            "network_bytes_out",
            "temperature_celsius",
            "power_watts",
            "load_average_1m",
            "load_average_5m",
            "load_average_15m",
            "disk_io_reads",
            "disk_io_writes",
            "process_count",
            "open_file_descriptors",
            "swap_usage_percent",
        ]

    @property
    def version(self) -> str:
        return "1.0.0"

    def validate_config(
        self,
        endpoint: str | None,
        port: int | None,
    ) -> bool:
        if port is not None and (
            port < 1 or port > 65535
        ):
            return False

        return True

    def collect(
        self,
        endpoint: str | None,
        port: int | None,
        metric_keys: list[str],
    ) -> list[CollectedMetric]:
        if not self.validate_config(endpoint, port):
            return []

        now = datetime.utcnow()
        collected = []

        for key in metric_keys:
            if key not in self.supported_metrics:
                continue

            value = self._query_agent_metric(
                endpoint,
                port,
                key,
            )

            if value is not None:
                collected.append(
                    CollectedMetric(
                        metric_key=key,
                        value=value,
                        unit=self._get_unit(key),
                        timestamp=now,
                    )
                )

        return collected

    def check_health(
        self,
        endpoint: str | None,
        port: int | None,
    ) -> HealthStatus:
        if not self.validate_config(endpoint, port):
            return HealthStatus(
                status="DOWN",
                message="Invalid agent configuration",
            )

        return HealthStatus(
            status="UP",
            response_time_ms=10.0,
            message="Agent reachable",
        )

    def _query_agent_metric(
        self,
        endpoint: str | None,
        port: int | None,
        metric_key: str,
    ) -> float | None:
        return None

    def _get_unit(self, metric_key: str) -> str | None:
        units = {
            "cpu_usage_percent": "%",
            "memory_usage_percent": "%",
            "disk_usage_percent": "%",
            "network_bytes_in": "bytes",
            "network_bytes_out": "bytes",
            "temperature_celsius": "C",
            "power_watts": "W",
            "load_average_1m": "load",
            "load_average_5m": "load",
            "load_average_15m": "load",
            "disk_io_reads": "ops",
            "disk_io_writes": "ops",
            "process_count": "count",
            "open_file_descriptors": "count",
            "swap_usage_percent": "%",
        }
        return units.get(metric_key)
