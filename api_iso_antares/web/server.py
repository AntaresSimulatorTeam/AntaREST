from typing import Any

from flask import Flask, jsonify, request, Response, send_file

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.engine import SwaggerEngine
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
        "/metadata/<path:path>",
        methods=["GET"],
    )
    def metadata(path: str) -> Any:
        global request_handler
        parameters = _construct_parameters(request.args)

        try:
            output = request_handler.get(path, parameters)
        except HtmlException as e:
            return e.message, e.html_code_error
        return jsonify(output), 200

    @application.route(
        "/file/<path:path>",
        methods=["GET"],
    )
    def data(path: str) -> Any:
        global request_handler

        try:
            file_path = str(request_handler.path_to_studies / path)
            return send_file(file_path)
        except FileNotFoundError:
            return f"{path} not found", 404

    @application.route(
        "/swagger",
        methods=["GET"],
    )
    def swagger() -> Any:
        global request_handler
        jsm = request_handler.get_jsm()
        swg_doc = SwaggerEngine.parse(jsm=jsm)
        return jsonify(swg_doc), 200

    @application.route(
        "/studies",
        methods=["GET"],
    )
    def studies() -> Any:
        global request_handler
        available_studies = request_handler.get_studies()
        return jsonify(available_studies), 200

    @application.after_request
    def after_request(response: Response) -> Response:
        header = response.headers
        header["Access-Control-Allow-Origin"] = "*"
        return response


def create_server(req: RequestHandler) -> Flask:
    global request_handler
    request_handler = req
    application = Flask(__name__)
    create_routes(application)
    return application
