import os
import re
from typing import Any
from http import HTTPStatus
from flask import Flask, jsonify, request, Response, send_file, escape

from api_iso_antares.custom_exceptions import HtmlException
from api_iso_antares.engine import SwaggerEngine
from api_iso_antares.web.request_handler import (
    RequestHandler,
    RequestHandlerParameters,
    StudyAlreadyExistError,
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
        "/file/<path:path>",
        methods=["GET"],
    )
    def get_file(path: str) -> Any:
        global request_handler

        try:
            file_path = request_handler.path_to_studies / path
            return send_file(file_path.absolute())
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
    def get_studies() -> Any:
        global request_handler
        available_studies = request_handler.get_studies_informations()
        return jsonify(available_studies), HTTPStatus.OK.value

    @application.route(
        "/studies/<path:path>",
        methods=["GET"],
    )
    def get_study(path: str) -> Any:
        global request_handler
        parameters = _construct_parameters(request.args)

        try:
            output = request_handler.get(path, parameters)
        except HtmlException as e:
            return e.message, e.html_code_error
        return jsonify(output), 200

    @application.route(
        "/studies/<string:name>/copy",
        methods=["POST"],
    )
    def copy_study(name: str) -> Any:
        global request_handler

        source_name = str(escape(name))
        destination_name = str(escape(str(request.args.get("dest"))))

        if request.args.get("dest") is None:
            content = "Copy operation need a dest query parameter."
            code = HTTPStatus.BAD_REQUEST.value

        elif request_handler.is_study_exist(destination_name):
            content = (
                f"A simulation already exist with the name {destination_name}."
            )
            code = HTTPStatus.CONFLICT.value

        elif not request_handler.is_study_exist(source_name):
            content = f"Study {source_name} does not exist."
            code = HTTPStatus.BAD_REQUEST.value

        else:
            request_handler.copy_study(src=source_name, dest=destination_name)
            content = "/studies/" + destination_name
            code = HTTPStatus.CREATED.value

        return content, code

    @application.route(
        "/studies/<string:name>",
        methods=["POST"],
    )
    def post_studies(name: str) -> Any:
        global request_handler

        if not re.match("^[a-zA-Z0-9-_]*$", name):
            return (
                "Study name can only contain alphanumeric characters with '-' or '_'",
                403,
            )

        try:
            request_handler.create_study(name)
            content = "/studies/" + name
            code = HTTPStatus.CREATED.value
        except StudyAlreadyExistError as e:
            content = e.message
            code = e.html_code_error

        return jsonify(content), code

    @application.route("/health", methods=["GET"])
    def health() -> Any:
        return jsonify({"status": "available"}), 200

    @application.route("/studies/<string:name>/export", methods=["GET"])
    def export_file(name: str) -> Any:
        global request_handler

        compact = "compact" in request.args

        # try:
        content = request_handler.export(name, compact)
        return send_file(
            content,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"{name}{'-compact' if compact else ''}.zip",
        )
        # except HtmlException as e:
        #     return e.message, e.html_code_error

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
