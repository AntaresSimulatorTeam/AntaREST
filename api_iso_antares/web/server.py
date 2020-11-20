import io
import re
from http import HTTPStatus
from typing import Any

from flask import escape, Flask, jsonify, request, Response, send_file

from api_iso_antares.custom_exceptions import (
    HtmlException,
    stop_and_return_on_html_exception,
)
from api_iso_antares.engine import SwaggerEngine
from api_iso_antares.web.request_handler import (
    RequestHandler,
    RequestHandlerParameters,
)

request_handler: RequestHandler


class BadStudyNameError(HtmlException):
    def __init__(self) -> None:
        super().__init__(
            "Study name can only contain alphanumeric characters with '-' or '_'",
            HTTPStatus.BAD_REQUEST.value,
        )


def _assert_study_name(name: str) -> None:
    if not re.match("^[a-zA-Z0-9-_]*$", name):
        raise BadStudyNameError


def sanitize_study_name(name: str) -> str:
    _assert_study_name(name)
    return escape(name)


def _construct_parameters(
    params: Any,
) -> RequestHandlerParameters:
    request_parameters = RequestHandlerParameters()
    request_parameters.depth = params.get(
        "depth", request_parameters.depth, type=int
    )
    return request_parameters


def create_study_routes(application: Flask) -> None:
    @application.route("/studies", methods=["GET"])
    def get_studies() -> Any:
        global request_handler
        available_studies = request_handler.get_studies_informations()
        return jsonify(available_studies), HTTPStatus.OK.value

    @application.route("/studies", methods=["POST"])
    def import_study() -> Any:
        global request_handler

        if not request.data:
            content = "No data provided."
            code = HTTPStatus.BAD_REQUEST.value
            return content, code

        zip_binary = io.BytesIO(request.data)

        uuid = request_handler.import_study(zip_binary)
        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @application.route(
        "/studies/<path:path>",
        methods=["GET"],
    )
    @stop_and_return_on_html_exception
    def get_study(path: str) -> Any:
        global request_handler
        parameters = _construct_parameters(request.args)

        output = request_handler.get(path, parameters)

        return jsonify(output), 200

    @application.route(
        "/studies/<string:name>/copy",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
    def copy_study(name: str) -> Any:
        global request_handler

        source_name = name
        destination_name = request.args.get("dest")

        if destination_name is None:
            content = "Copy operation need a dest query parameter."
            code = HTTPStatus.BAD_REQUEST.value
            return content, code

        source_name = sanitize_study_name(source_name)
        destination_name = sanitize_study_name(destination_name)

        request_handler.copy_study(src=source_name, dest=destination_name)
        content = "/studies/" + destination_name
        code = HTTPStatus.CREATED.value

        return content, code

    @application.route(
        "/studies/<string:name>",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
    def post_study(name: str) -> Any:
        global request_handler

        name = sanitize_study_name(name)

        request_handler.create_study(name)
        content = "/studies/" + name
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @application.route("/studies/<string:name>/export", methods=["GET"])
    @stop_and_return_on_html_exception
    def export_study(name: str) -> Any:
        global request_handler

        name = sanitize_study_name(name)
        compact = "compact" in request.args

        content = request_handler.export_study(name, compact)

        return send_file(
            content,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"{name}{'-compact' if compact else ''}.zip",
        )

    @application.route("/studies/<string:name>", methods=["DELETE"])
    @stop_and_return_on_html_exception
    def delete_study(name: str) -> Any:
        global request_handler

        name = sanitize_study_name(name)

        request_handler.delete_study(name)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code


def create_non_business_routes(application: Flask) -> None:
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

    @application.route("/health", methods=["GET"])
    def health() -> Any:
        return jsonify({"status": "available"}), 200

    @application.after_request
    def after_request(response: Response) -> Response:
        header = response.headers
        header["Access-Control-Allow-Origin"] = "*"
        return response


def create_routes(application: Flask) -> None:
    create_study_routes(application)
    create_non_business_routes(application)


def create_server(req: RequestHandler) -> Flask:
    global request_handler
    request_handler = req
    application = Flask(__name__)
    create_routes(application)
    return application
