from pathlib import Path
from typing import Optional

from flask import Flask

from antarest.storage_api.antares_io.exporter.export_file import Exporter
from antarest.storage_api.filesystem.factory import StudyFactory
from antarest.storage_api.web import RequestHandler
from antarest.storage_api.web.studies_blueprint import create_study_routes
from antarest.storage_api.web.ui_blueprint import create_ui
from antarest.storage_api.web.utils_blueprint import create_utils_routes


def build_storage(
    application: Flask,
    res: Path,
    studies_path: Path = Path(),
    req: Optional[RequestHandler] = None,
):
    request_handler = req or RequestHandler(
        study_factory=StudyFactory(),
        exporter=Exporter(),
        path_studies=studies_path,
        path_resources=res,
    )

    application.register_blueprint(create_ui(res, request_handler))
    application.register_blueprint(create_study_routes(request_handler))
    application.register_blueprint(create_utils_routes(request_handler))
