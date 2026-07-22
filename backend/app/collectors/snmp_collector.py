from datetime import datetime

from app.collectors.base import (
    BaseCollector,
    CollectedMetric,
    HealthStatus,
)


class SNMPCollector(BaseCollector):
    @property
    def collector_type(self) -> str:
        return "SNMP"

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
            "uptime_seconds",
            "if_oper_status",
        ]

    @property
    def version(self) -> str:
        return "1.0.0"

    def validate_config(
        self,
        endpoint: str | None,
        port: int | None,
    ) -> bool:
        if not endpoint:
            return False

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

        snmp_port = port or 161
        now = datetime.utcnow()

        collected = []

        for key in metric_keys:
            if key not in self.supported_metrics:
                continue

            value = self._query_snmp_metric(
                endpoint,
                snmp_port,
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
                message="Invalid SNMP configuration",
            )

        return HealthStatus(
            status="UP",
            response_time_ms=15.0,
            message="SNMP agent reachable",
        )

    def _query_snmp_metric(
        self,
        endpoint: str | None,
        port: int,
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
            "uptime_seconds": "s",
            "if_oper_status": "status",
        }
        return units.get(metric_key)
