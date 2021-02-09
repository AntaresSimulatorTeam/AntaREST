from pathlib import Path
from typing import Optional

from flask import Flask

from antarest.common.config import Config
from antarest.storage.repository.antares_io.exporter.export_file import (
    Exporter,
)
from antarest.storage.repository.filesystem.factory import StudyFactory
from antarest.storage.web import RequestHandler
from antarest.storage.web.studies_blueprint import create_study_routes
from antarest.storage.web.ui_blueprint import create_ui
from antarest.storage.web.utils_blueprint import create_utils_routes


def build_storage(
    application: Flask,
    config: Config,
    req: Optional[RequestHandler] = None,
) -> None:

    request_handler = req or RequestHandler(
        study_factory=StudyFactory(), exporter=Exporter(), config=config
    )

    application.register_blueprint(create_ui(request_handler, config))
    application.register_blueprint(create_study_routes(request_handler))
    application.register_blueprint(create_utils_routes(request_handler))
