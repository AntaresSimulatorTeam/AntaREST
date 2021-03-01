import subprocess
from http import HTTPStatus
from pathlib import Path
from typing import Any, Optional

from flask import Blueprint, send_file, request, jsonify, Response

from antarest.common.auth import Auth
from antarest.common.config import Config
from antarest.login.model import User
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)
from antarest.storage.service import StorageService
from antarest import __version__


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


def create_utils_routes(
    storage_service: StorageService, config: Config
) -> Blueprint:
    bp = Blueprint("create_utils", __name__)
    auth = Auth(config)

    @bp.route(
        "/file/<path:path>",
        methods=["GET"],
    )
    @auth.protected()
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
            file_path = storage_service.study_service.path_to_studies / path
            return send_file(file_path.absolute())
        except FileNotFoundError:
            return f"{path} not found", HTTPStatus.NOT_FOUND.value

    @bp.route(
        "/file/<path:path>",
        methods=["POST"],
    )
    @auth.protected()
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
        params = StorageServiceParameters(user=Auth.get_current_user())
        storage_service.upload_matrix(path, data, params)
        output = b""
        code = HTTPStatus.NO_CONTENT.value

        return output, code

    @bp.route("/health", methods=["GET"])
    def health() -> Any:
        return jsonify({"status": "available"}), 200

    @bp.route("/version", methods=["GET"])
    def version() -> Any:
        """
        Get application version
        ---
        responses:
          '200':
            content:
              application/json:
                schema:
                    type: object
                    properties:
                        version:
                            type: string
                            description: Semantic version
                        gitcommit:
                            type: string
                            description: Build version (git commit id)
            description: Successful operation
        tags:
          - Misc
        """
        version_data = {"version": __version__}

        commit_id = get_commit_id(storage_service.study_service.path_resources)
        if commit_id is not None:
            version_data["gitcommit"] = commit_id

        return jsonify(version_data), HTTPStatus.OK.value

    @bp.after_request
    def after_request(response: Response) -> Response:
        header = response.headers
        header["Access-Control-Allow-Origin"] = "*"
        return response

    return bp
