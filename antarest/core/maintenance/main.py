from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.core.maintenance.repository import MaintenanceRepository
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.maintenance.web import create_maintenance_api


def build_maintenance_manager(
    application: Optional[FastAPI],
    config: Config,
    cache: ICache,
    event_bus: IEventBus = DummyEventBusService(),
) -> MaintenanceService:

    repository = MaintenanceRepository()
    service = MaintenanceService(config, repository, event_bus, cache)

    if application:
        application.include_router(create_maintenance_api(service, config))

    return service
