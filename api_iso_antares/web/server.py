from typing import Any, Dict

from flask import Flask, jsonify, request

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.web.request_handler import (
    RequestHandler,
    RequestHandlerParameters,
)

request_handler: RequestHandler


def _construct_parameters(
    params: Any,
) -> RequestHandlerParameters:
    request_parameters = RequestHandlerParameters()
    request_parameters.depth = params.get(
        "depth", request_parameters.depth, type=int
    )
    return request_parameters


def create_routes(application: Flask) -> None:
    @application.route(
        "/api/studies/<path:path>",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )
    def studies(path: str) -> Any:
        global request_handler

        parameters = _construct_parameters(request.args)

        try:
            output = request_handler.get(path, parameters)
        except HtmlException as e:
            return e.message, e.html_code_error
        return jsonify(output), 200


def create_server(req: RequestHandler) -> Flask:
    global request_handler
    request_handler = req
    application = Flask(__name__)
    create_routes(application)
    return application
