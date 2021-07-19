from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.launcher.repository import JobResultRepository
from antarest.launcher.service import LauncherService
from antarest.launcher.web import create_launcher_api
from antarest.storage.service import StudyService


def build_launcher(
    application: FastAPI,
    config: Config,
    service_storage: Optional[StudyService] = None,
    service_launcher: Optional[LauncherService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> None:

    if service_storage and not service_launcher:
        repository = JobResultRepository()
        service_launcher = LauncherService(
            config=config,
            storage_service=service_storage,
            repository=repository,
            event_bus=event_bus,
        )

    if service_launcher:
        application.include_router(
            create_launcher_api(service_launcher, config)
        )
