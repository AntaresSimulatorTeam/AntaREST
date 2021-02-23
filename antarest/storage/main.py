from pathlib import Path
from typing import Optional

from flask import Flask

from antarest.common.config import Config
from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.importer_service import ImporterService
from antarest.storage.business.study_service import StudyService
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
    study_factory: Optional[StudyFactory] = None,
    exporter: Optional[Exporter] = None,
    storage_service: Optional[StorageService] = None,
) -> StorageService:

    path_to_studies = Path(config["storage.studies"])
    path_resources = Path(config["_internal.resources_path"])
    study_factory = study_factory or StudyFactory()
    exporter = exporter or Exporter()

    study_service = StudyService(
        path_to_studies=path_to_studies,
        study_factory=study_factory,
        path_resources=path_resources,
    )
    importer_service = ImporterService(
        path_to_studies=path_to_studies,
        study_service=study_service,
        study_factory=study_factory,
    )
    exporter_service = ExporterService(
        path_to_studies=path_to_studies,
        study_service=study_service,
        study_factory=study_factory,
        exporter=exporter,
    )

    storage_service = storage_service or StorageService(
        study_service=study_service,
        importer_service=importer_service,
        exporter_service=exporter_service,
    )

    application.register_blueprint(
        create_study_routes(storage_service, config)
    )
    application.register_blueprint(
        create_utils_routes(storage_service, config)
    )

    return storage_service
