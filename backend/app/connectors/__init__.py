from app.connectors.base import BaseConnector
from app.connectors.ssh_connector import SSHConnector
from app.connectors.snmp_connector import SNMPConnector
from app.connectors.api_connector import APIConnector
from app.connectors.ansible_connector import AnsibleConnector


CONNECTOR_MAP = {
    "SSH": SSHConnector,
    "SNMP": SNMPConnector,
    "API": APIConnector,
    "ANSIBLE": AnsibleConnector,
}


def create_connector(
    connector_type: str,
    hostname: str,
    port: int = 22,
    username: str = "",
    password: str | None = None,
    **kwargs,
) -> BaseConnector:
    cls = CONNECTOR_MAP.get(connector_type.upper())
    if cls is None:
        raise ValueError(
            f"Unknown connector type: {connector_type}"
        )
    return cls(
        hostname=hostname,
        port=port,
        username=username,
        password=password,
        **kwargs,
    )


def get_supported_connector_types() -> list[str]:
    return list(CONNECTOR_MAP.keys())
