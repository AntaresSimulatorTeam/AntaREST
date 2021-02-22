from typing import Optional

from flask import Flask
from sqlalchemy.orm import Session  # type: ignore

from antarest.common.config import Config
from antarest.launcher.repository import JobResultRepository
from antarest.launcher.service import LauncherService
from antarest.launcher.web import create_launcher_api
from antarest.storage.service import StorageService


def build_launcher(
    application: Flask,
    config: Config,
    db_session: Session,
    service_storage: Optional[StorageService] = None,
    service_launcher: Optional[LauncherService] = None,
) -> None:

    if service_storage and not service_launcher:
        repository = JobResultRepository(session=db_session)
        service_launcher = LauncherService(
            config=config,
            storage_service=service_storage,
            repository=repository,
        )

    if service_launcher:
        application.register_blueprint(create_launcher_api(service_launcher))
