from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.core.tasks.service import ITaskService
from antarest.launcher.repository import JobResultRepository
from antarest.launcher.service import LauncherService
from antarest.launcher.web import create_launcher_api
from antarest.study.service import StudyService


def build_launcher(
    application: Optional[FastAPI],
    config: Config,
    study_service: StudyService,
    file_transfer_manager: FileTransferManager,
    task_service: ITaskService,
    event_bus: IEventBus = DummyEventBusService(),
    service_launcher: Optional[LauncherService] = None,
) -> Optional[LauncherService]:

    if not service_launcher:
        repository = JobResultRepository()
        study_service.add_on_deletion_callback(repository.delete_by_study_id)
        service_launcher = LauncherService(
            config=config,
            study_service=study_service,
            job_result_repository=repository,
            event_bus=event_bus,
            file_transfer_manager=file_transfer_manager,
            task_service=task_service,
        )

    if service_launcher and application:
        application.include_router(
            create_launcher_api(service_launcher, config)
        )

    return service_launcher
