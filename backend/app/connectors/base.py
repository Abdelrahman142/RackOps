from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConnectorResult:
    success: bool
    output: str
    error_message: str | None = None
    executed_at: datetime = field(
        default_factory=datetime.utcnow
    )
    execution_time_ms: int | None = None


class BaseConnector(ABC):
    def __init__(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None = None,
    ):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self._connected = False

    @abstractmethod
    def connect(self) -> ConnectorResult:
        pass

    @abstractmethod
    def execute(
        self, command: str, parameters: str | None = None
    ) -> ConnectorResult:
        pass

    @abstractmethod
    def disconnect(self) -> ConnectorResult:
        pass

    def test_connection(self) -> ConnectorResult:
        result = self.connect()
        if result.success:
            self.disconnect()
        return result

    @property
    def is_connected(self) -> bool:
        return self._connected
