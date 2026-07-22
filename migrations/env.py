import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.database.base import Base
from app.models.company import Company  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.datacenter import DataCenter  # noqa: F401
from app.models.building import Building  # noqa: F401
from app.models.floor import Floor  # noqa: F401
from app.models.room import Room  # noqa: F401
from app.models.rack import Rack  # noqa: F401
from app.models.device import Device  # noqa: F401
from app.models.ups import UPS  # noqa: F401
from app.models.pdu import PDU  # noqa: F401
from app.models.power_feed import PowerFeed  # noqa: F401
from app.models.cooling_unit import CoolingUnit  # noqa: F401
from app.models.environmental_zone import EnvironmentalZone  # noqa: F401
from app.models.sensor import Sensor  # noqa: F401
from app.models.network_interface import NetworkInterface  # noqa: F401
from app.models.physical_connection import PhysicalConnection  # noqa: F401
from app.models.vlan import VLAN  # noqa: F401
from app.models.subnet import Subnet  # noqa: F401
from app.models.ip_address import IPAddress  # noqa: F401
from app.models.monitoring_target import MonitoringTarget  # noqa: F401
from app.models.metric_definition import MetricDefinition  # noqa: F401
from app.models.metric_data import MetricData  # noqa: F401
from app.models.health_check import HealthCheck  # noqa: F401
from app.models.alert_rule import AlertRule  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.incident import AlertIncident  # noqa: F401
from app.models.maintenance_window import MaintenanceWindow  # noqa: F401
from app.models.automation_job import AutomationJob  # noqa: F401
from app.models.device_connector import DeviceConnector  # noqa: F401
from app.models.automation_task import AutomationTask  # noqa: F401
from app.models.configuration_backup import ConfigurationBackup  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

config = context.config
config.set_main_option(
    "sqlalchemy.url", settings.DATABASE_URL
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
