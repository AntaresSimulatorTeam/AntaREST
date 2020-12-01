import io
import json
import re
from http import HTTPStatus
from typing import Any

from flask import escape, Flask, jsonify, request, Response, send_file

from api_iso_antares.web.html_exception import (
    HtmlException,
    stop_and_return_on_html_exception,
)
from api_iso_antares.engine import SwaggerEngine
from api_iso_antares.web.request_handler import (
    RequestHandler,
    RequestHandlerParameters,
)

request_handler: RequestHandler


class BadUUIDError(HtmlException):
    def __init__(self) -> None:
        super().__init__(
            "Study's UUID can only contain alphanumeric characters with '-'",
            HTTPStatus.BAD_REQUEST.value,
        )


def _assert_uuid(uuid: str) -> None:
    if not re.match("^[a-zA-Z0-9-]*$", uuid):
        raise BadUUIDError


def sanitize_uuid(uuid: str) -> str:
    _assert_uuid(uuid)
    return escape(uuid)


def sanitize_study_name(name: str) -> str:
    return sanitize_uuid(name)


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
        "/studies/<string:uuid>/copy",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
    def copy_study(uuid: str) -> Any:
        global request_handler

        source_uuid = uuid
        destination_study_name = request.args.get("dest")

        if destination_study_name is None:
            content = "Copy operation need a dest query parameter."
            code = HTTPStatus.BAD_REQUEST.value
            return content, code

        source_uuid_sanitized = sanitize_uuid(source_uuid)
        destination_name_sanitized = sanitize_study_name(
            destination_study_name
        )

        destination_uuid = request_handler.copy_study(
            src_uuid=source_uuid_sanitized,
            dest_study_name=destination_name_sanitized,
        )
        content = "/studies/" + destination_uuid
        code = HTTPStatus.CREATED.value

        return content, code

    @application.route(
        "/studies/<string:name>",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
    def create_study(name: str) -> Any:
        global request_handler

        name_sanitized = sanitize_study_name(name)

        uuid = request_handler.create_study(name_sanitized)

        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @application.route("/studies/<string:uuid>/export", methods=["GET"])
    @stop_and_return_on_html_exception
    def export_study(uuid: str) -> Any:
        global request_handler

        uuid_sanitized = sanitize_uuid(uuid)
        compact = "compact" in request.args

        content = request_handler.export_study(uuid_sanitized, compact)

        return send_file(
            content,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"{uuid_sanitized}{'-compact' if compact else ''}.zip",
        )

    @application.route("/studies/<string:uuid>", methods=["DELETE"])
    @stop_and_return_on_html_exception
    def delete_study(uuid: str) -> Any:
        global request_handler

        uuid_sanitized = sanitize_uuid(uuid)

        request_handler.delete_study(uuid_sanitized)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @application.route("/studies/<path:path>", methods=["POST"])
    @stop_and_return_on_html_exception
    def edit_study(path: str) -> Any:
        global request_handler

        new = json.loads(request.data)
        if not new:
            raise HtmlException("empty body not authorized", 400)

        request_handler.edit_study(path, new)
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
            return f"{path} not found", HTTPStatus.NOT_FOUND.value

    @application.route(
        "/file/<path:path>",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
    def post_file(path: str) -> Any:
        global request_handler

        request_handler.upload_matrix(path, request.data)
        output = b""
        code = HTTPStatus.NO_CONTENT.value

        return output, code

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
