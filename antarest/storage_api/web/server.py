import os
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    jsonify,
    request,
)
from flask_swagger import swagger  # type: ignore
from flask_swagger_ui import get_swaggerui_blueprint  # type: ignore

from antarest.storage_api.web.request_handler import (
    RequestHandler,
)
from antarest.storage_api.web.studies_blueprint import create_study_routes
from antarest.storage_api.web.swagger import update
from antarest.storage_api.web.ui_blueprint import create_ui
from antarest.storage_api.web.utils_blueprint import create_utils_routes


def create_swagger(application: Any) -> None:
    @application.route(  # type: ignore
        "/swagger.json",
        methods=["GET"],
    )
    def spec() -> Any:
        specification = update(swagger(application))
        specification["servers"] = [{"url": request.url_root}]

        return jsonify(specification)

    swaggerui_blueprint = get_swaggerui_blueprint(
        "/docs",
        "/swagger.json",
        config={"app_name": "Test application", "validatorUrl": None},
    )
    application.register_blueprint(swaggerui_blueprint)


def create_server(req: RequestHandler, res: Path) -> Flask:
    request_handler = req
    print(Path(os.curdir).absolute())
    application = Flask(__name__)
    application.register_blueprint(create_ui(res, request_handler))
    application.register_blueprint(create_study_routes(request_handler))
    application.register_blueprint(create_utils_routes(request_handler))

    create_swagger(application)
    return application
