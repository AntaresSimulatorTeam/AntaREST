from typing import Optional

from flask import Flask

from antarest.common.config import Config
from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.service import StorageService
from antarest.storage.web.studies_blueprint import create_study_routes
from antarest.storage.web.utils_blueprint import create_utils_routes


def build_storage(
    application: Flask,
    config: Config,
    storage_service: Optional[StorageService] = None,
) -> None:

    storage_service = storage_service or StorageService(
        study_factory=StudyFactory(), exporter=Exporter(), config=config
    )

    application.register_blueprint(
        create_study_routes(storage_service, config)
    )
    application.register_blueprint(
        create_utils_routes(storage_service, config)
    )
