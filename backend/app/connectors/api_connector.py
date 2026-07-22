import time
from datetime import datetime

from app.connectors.base import (
    BaseConnector,
    ConnectorResult,
)


class APIConnector(BaseConnector):
    def __init__(
        self,
        hostname: str,
        port: int = 443,
        username: str = "",
        password: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        use_https: bool = True,
        timeout: int = 30,
    ):
        super().__init__(
            hostname, port, username, password
        )
        self.base_url = base_url or (
            f"{'https' if use_https else 'http'}://{hostname}:{port}"
        )
        self.api_key = api_key
        self.timeout = timeout
        self._session = None

    def connect(self) -> ConnectorResult:
        start = time.time()
        try:
            import httpx

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.username and self.password:
                import base64

                creds = base64.b64encode(
                    f"{self.username}:{self.password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {creds}"

            session = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                verify=False,
            )
            resp = session.get("/api/system/status")
            elapsed = int((time.time() - start) * 1000)

            if resp.status_code == 200:
                self._session = session
                self._connected = True
                return ConnectorResult(
                    success=True,
                    output=f"API connection established: {resp.status_code}",
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            else:
                session.close()
                return ConnectorResult(
                    success=False,
                    output="",
                    error_message=f"HTTP {resp.status_code}: {resp.text[:500]}",
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
        except ImportError:
            return ConnectorResult(
                success=False,
                output="",
                error_message="httpx is not installed",
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
        if not self._connected or self._session is None:
            return ConnectorResult(
                success=False,
                output="",
                error_message="Not connected",
            )
        start = time.time()
        try:
            import json

            method = "GET"
            path = command
            body = None

            if parameters:
                try:
                    params = json.loads(parameters)
                    method = params.pop("_method", "GET")
                    path = params.pop("_path", command)
                    body = params if params else None
                except (json.JSONDecodeError, TypeError):
                    pass

            if method == "POST":
                resp = self._session.post(path, json=body)
            elif method == "PUT":
                resp = self._session.put(path, json=body)
            elif method == "DELETE":
                resp = self._session.delete(path)
            else:
                resp = self._session.get(path)

            elapsed = int((time.time() - start) * 1000)

            if resp.status_code < 400:
                return ConnectorResult(
                    success=True,
                    output=resp.text[:10000],
                    executed_at=datetime.utcnow(),
                    execution_time_ms=elapsed,
                )
            else:
                return ConnectorResult(
                    success=False,
                    output=resp.text[:10000],
                    error_message=f"HTTP {resp.status_code}",
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
            if self._session:
                self._session.close()
            self._connected = False
            self._session = None
            return ConnectorResult(
                success=True,
                output="API session closed",
            )
        except Exception as e:
            self._connected = False
            self._session = None
            return ConnectorResult(
                success=False,
                output="",
                error_message=str(e),
            )
