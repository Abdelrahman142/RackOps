import time
from datetime import datetime

from app.connectors.base import (
    BaseConnector,
    ConnectorResult,
)


class SNMPConnector(BaseConnector):
    def __init__(
        self,
        hostname: str,
        port: int = 161,
        username: str = "",
        password: str | None = None,
        community: str = "public",
        version: int = 2,
        timeout: int = 10,
    ):
        super().__init__(
            hostname, port, username, password
        )
        self.community = community
        self.version = version
        self.timeout = timeout
        self._session = None

    def connect(self) -> ConnectorResult:
        start = time.time()
        try:
            from pysnmp.hlapi import (
                SnmpEngine,
                CommunityData,
                UdpTransportTarget,
                ContextData,
                ObjectType,
                ObjectIdentity,
                get_cmd,
            )

            snmp_engine = SnmpEngine()
            error_indication, error_status, error_index, var_binds = next(
                get_cmd(
                    snmp_engine,
                    CommunityData(self.community),
                    UdpTransportTarget(
                        (self.hostname, self.port),
                        timeout=self.timeout,
                    ),
                    ContextData(),
                    ObjectType(
                        ObjectIdentity("1.3.6.1.2.1.1.1.0")
                    ),
                )
            )
            elapsed = int((time.time() - start) * 1000)

            if error_indication:
                return ConnectorResult(
                    success=False,
                    output="",
                    error_message=str(error_indication),
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            elif error_status:
                return ConnectorResult(
                    success=False,
                    output="",
                    error_message=f"{error_status.prettyPrint()} at {error_index}",
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            else:
                self._session = snmp_engine
                self._connected = True
                output = ", ".join(
                    f"{x[0]}={x[1]}" for x in var_binds
                )
                return ConnectorResult(
                    success=True,
                    output=output,
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
        except ImportError:
            return ConnectorResult(
                success=False,
                output="",
                error_message="pysnmp is not installed",
            )
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return ConnectorResult(
                success=False,
                output="",
                error_message=str(e),
                executed_at=datetime.utcnow(),
                execution_time_ms=elapsed,
            )

    def execute(
        self, command: str, parameters: str | None = None
    ) -> ConnectorResult:
        if not self._connected:
            return ConnectorResult(
                success=False,
                output="",
                error_message="Not connected",
            )
        start = time.time()
        try:
            from pysnmp.hlapi import (
                ObjectType,
                ObjectIdentity,
                get_cmd,
                SnmpEngine,
                CommunityData,
                UdpTransportTarget,
                ContextData,
            )

            oid = command if parameters is None else parameters
            snmp_engine = self._session or SnmpEngine()
            error_indication, error_status, error_index, var_binds = next(
                get_cmd(
                    snmp_engine,
                    CommunityData(self.community),
                    UdpTransportTarget(
                        (self.hostname, self.port),
                        timeout=self.timeout,
                    ),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )
            elapsed = int((time.time() - start) * 1000)

            if error_indication:
                return ConnectorResult(
                    success=False,
                    output="",
                    error_message=str(error_indication),
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            elif error_status:
                return ConnectorResult(
                    success=False,
                    output="",
                    error_message=f"{error_status.prettyPrint()}",
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            else:
                output = ", ".join(
                    f"{x[0]}={x[1]}" for x in var_binds
                )
                return ConnectorResult(
                    success=True,
                    output=output,
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return ConnectorResult(
                success=False,
                output="",
                error_message=str(e),
                executed_at=datetime.utcnow(),
                execution_time_ms=elapsed,
            )

    def disconnect(self) -> ConnectorResult:
        self._connected = False
        self._session = None
        return ConnectorResult(
            success=True,
            output="SNMP session closed",
        )
