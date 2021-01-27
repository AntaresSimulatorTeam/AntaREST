from http import HTTPStatus
from typing import Any

from flask import Blueprint, send_file, request, jsonify, Response

from AntaREST.storage_api.web import RequestHandler
from AntaREST.storage_api.web.html_exception import (
    stop_and_return_on_html_exception,
)
from AntaREST.storage_api import __version__


def create_utils_routes(request_handler: RequestHandler) -> Blueprint:
    bp = Blueprint("create_utils", __name__)

    @bp.route(
        "/file/<path:path>",
        methods=["GET"],
    )
    def get_file(path: str) -> Any:
        """
        Get file
        ---
        responses:
            '200':
              content:
                application/octet-stream: {}
              description: Successful operation
            '404':
              description: File not found
        parameters:
          - in: path
            name: path
            required: true
            schema:
                type: string
        tags:
          - Manage Matrix

        """

        try:
            file_path = request_handler.path_to_studies / path
            return send_file(file_path.absolute())
        except FileNotFoundError:
            return f"{path} not found", HTTPStatus.NOT_FOUND.value

    @bp.route(
        "/file/<path:path>",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
    def post_file(path: str) -> Any:
        """
        Post file
        ---
        parameters:
          - in: path
            name: path
            required: true
            schema:
              type: string
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        tags:
          - Manage Matrix
        """

        data = request.files["matrix"].read()
        request_handler.upload_matrix(path, data)
        output = b""
        code = HTTPStatus.NO_CONTENT.value

        return output, code

    @bp.route("/health", methods=["GET"])
    def health() -> Any:
        return jsonify({"status": "available"}), 200

    @bp.route("/version", methods=["GET"])
    def version() -> Any:
        version_data = {"version": __version__}
        return jsonify(version_data), HTTPStatus.OK.value

    @bp.after_request
    def after_request(response: Response) -> Response:
        header = response.headers
        header["Access-Control-Allow-Origin"] = "*"
        return response

    return bp
