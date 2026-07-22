import time
from datetime import datetime

from app.connectors.base import (
    BaseConnector,
    ConnectorResult,
)


class AnsibleConnector(BaseConnector):
    def __init__(
        self,
        hostname: str,
        port: int = 22,
        username: str = "",
        password: str | None = None,
        become: bool = False,
        become_method: str = "sudo",
        become_user: str = "root",
        extra_vars: dict | None = None,
        timeout: int = 60,
    ):
        super().__init__(
            hostname, port, username, password
        )
        self.become = become
        self.become_method = become_method
        self.become_user = become_user
        self.extra_vars = extra_vars or {}
        self.timeout = timeout

    def connect(self) -> ConnectorResult:
        start = time.time()
        try:
            result = self.test_connection()
            elapsed = int((time.time() - start) * 1000)
            if result.success:
                self._connected = True
            return ConnectorResult(
                success=result.success,
                output=result.output or "Ansible target reachable",
                error_message=result.error_message,
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

    def execute(
        self, command: str, parameters: str | None = None
    ) -> ConnectorResult:
        start = time.time()
        try:
            import json
            import subprocess

            cmd_parts = [
                "ansible",
                self.hostname,
                "-m", command,
                "-u", self.username,
                "--timeout", str(self.timeout),
            ]

            if self.password:
                cmd_parts.extend(["--ask-pass"])

            if self.become:
                cmd_parts.extend([
                    "--become",
                    "--become-method", self.become_method,
                    "--become-user", self.become_user,
                ])

            if parameters:
                cmd_parts.extend(["-a", parameters])

            if self.extra_vars:
                cmd_parts.extend([
                    "-e", json.dumps(self.extra_vars)
                ])

            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,
            )
            elapsed = int((time.time() - start) * 1000)

            if result.returncode == 0:
                return ConnectorResult(
                    success=True,
                    output=result.stdout.strip(),
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            else:
                return ConnectorResult(
                    success=False,
                    output=result.stdout.strip(),
                    error_message=result.stderr.strip(),
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
        except FileNotFoundError:
            return ConnectorResult(
                success=False,
                output="",
                error_message="ansible executable not found",
                executed_at=datetime.utcnow(),
                execution_time_ms=int((time.time() - start) * 1000),
            )
        except subprocess.TimeoutExpired:
            return ConnectorResult(
                success=False,
                output="",
                error_message="Ansible command timed out",
                executed_at=datetime.utcnow(),
                execution_time_ms=int((time.time() - start) * 1000),
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
        return ConnectorResult(
            success=True,
            output="Ansible session ended",
        )
