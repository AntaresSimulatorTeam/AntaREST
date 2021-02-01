import subprocess
from http import HTTPStatus
from pathlib import Path
from typing import Any, Optional

from flask import Blueprint, send_file, request, jsonify, Response

from antarest.storage_api.web import RequestHandler
from antarest.storage_api.web.html_exception import (
    stop_and_return_on_html_exception,
)
from antarest.storage_api import __version__


def get_commit_id(path_resources: Path) -> Optional[str]:

    commit_id = None

    path_commit_id = path_resources / "commit_id"
    if path_commit_id.exists():
        commit_id = path_commit_id.read_text()[:-1]
    else:
        command = "git log -1 HEAD --format=%H"
        process = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
        if process.returncode == 0:
            commit_id = process.stdout.decode("utf-8")

    if commit_id is not None:

        def remove_carriage_return(value: str) -> str:
            return value[:-1]

        commit_id = remove_carriage_return(commit_id)

    return commit_id


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

        commit_id = get_commit_id(request_handler.path_resources)
        if commit_id is not None:
            version_data["gitcommit"] = commit_id

        return jsonify(version_data), HTTPStatus.OK.value

    @bp.after_request
    def after_request(response: Response) -> Response:
        header = response.headers
        header["Access-Control-Allow-Origin"] = "*"
        return response

    return bp
