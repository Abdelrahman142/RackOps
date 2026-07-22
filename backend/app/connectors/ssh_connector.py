import time
from datetime import datetime

from app.connectors.base import (
    BaseConnector,
    ConnectorResult,
)


class SSHConnector(BaseConnector):
    def __init__(
        self,
        hostname: str,
        port: int = 22,
        username: str = "",
        password: str | None = None,
        timeout: int = 30,
    ):
        super().__init__(
            hostname, port, username, password
        )
        self.timeout = timeout
        self._client = None

    def connect(self) -> ConnectorResult:
        start = time.time()
        try:
            import paramiko

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
            )
            self._client = client
            self._connected = True
            elapsed = int((time.time() - start) * 1000)
            return ConnectorResult(
                success=True,
                output="SSH connection established",
                executed_at=datetime.utcnow(),
                execution_time_ms=elapsed,
            )
        except ImportError:
            return ConnectorResult(
                success=False,
                output="",
                error_message="paramiko is not installed",
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
        if not self._connected or self._client is None:
            return ConnectorResult(
                success=False,
                output="",
                error_message="Not connected",
            )
        start = time.time()
        try:
            full_cmd = command
            if parameters:
                full_cmd = f"{command} {parameters}"

            stdin, stdout, stderr = (
                self._client.exec_command(
                    full_cmd, timeout=self.timeout
                )
            )
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode("utf-8", errors="replace")
            error = stderr.read().decode("utf-8", errors="replace")
            elapsed = int((time.time() - start) * 1000)

            if exit_status == 0:
                return ConnectorResult(
                    success=True,
                    output=output.strip(),
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            else:
                return ConnectorResult(
                    success=False,
                    output=output.strip(),
                    error_message=error.strip() or f"Exit code: {exit_status}",
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
        try:
            if self._client:
                self._client.close()
            self._connected = False
            self._client = None
            return ConnectorResult(
                success=True,
                output="SSH connection closed",
            )
        except Exception as e:
            self._connected = False
            self._client = None
            return ConnectorResult(
                success=False,
                output="",
                error_message=str(e),
            )
