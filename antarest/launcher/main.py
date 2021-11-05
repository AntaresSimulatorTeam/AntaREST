from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.launcher.repository import JobResultRepository
from antarest.launcher.service import LauncherService
from antarest.launcher.web import create_launcher_api
from antarest.study.service import StudyService


def build_launcher(
    application: FastAPI,
    config: Config,
    study_service: Optional[StudyService] = None,
    service_launcher: Optional[LauncherService] = None,
    event_bus: IEventBus = DummyEventBusService(),
) -> Optional[LauncherService]:

    if study_service and not service_launcher:
        repository = JobResultRepository()
        study_service.add_callback(repository.delete_by_study_id)
        service_launcher = LauncherService(
            config=config,
            study_service=study_service,
            job_result_repository=repository,
            event_bus=event_bus,
        )

    if service_launcher:
        application.include_router(
            create_launcher_api(service_launcher, config)
        )

    return service_launcher
