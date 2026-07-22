from app.collectors.agent_collector import (
    AgentCollector,
)
from app.collectors.base import (
    BaseCollector,
    CollectedMetric,
    HealthStatus,
)
from app.collectors.prometheus_collector import (
    PrometheusCollector,
)
from app.collectors.snmp_collector import (
    SNMPCollector,
)

COLLECTOR_REGISTRY: dict[str, type[BaseCollector]] = {
    "SNMP": SNMPCollector,
    "PROMETHEUS": PrometheusCollector,
    "AGENT": AgentCollector,
}


def get_collector(
    collector_type: str,
) -> BaseCollector | None:
    cls = COLLECTOR_REGISTRY.get(collector_type)
    if cls is None:
        return None
    return cls()


def list_collector_types() -> list[str]:
    return list(COLLECTOR_REGISTRY.keys())
