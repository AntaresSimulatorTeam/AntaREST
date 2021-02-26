import io
import json
from http import HTTPStatus
from typing import Any

from flask import (
    escape,
    jsonify,
    request,
    send_file,
    Blueprint,
)
from werkzeug.exceptions import BadRequest

from antarest.common.auth import Auth
from antarest.common.config import Config
from antarest.login.model import User
from antarest.storage.service import StorageService
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)

storage_service: StorageService


def sanitize_uuid(uuid: str) -> str:
    return escape(uuid)


def sanitize_study_name(name: str) -> str:
    return sanitize_uuid(name)


def _construct_parameters(params: Any, user: User) -> StorageServiceParameters:
    request_parameters = StorageServiceParameters(user=user)
    request_parameters.depth = params.get(
        "depth", request_parameters.depth, type=int
    )
    return request_parameters


def create_study_routes(
    storage_service: StorageService, config: Config
) -> Blueprint:
    bp = Blueprint("create_study_route", __name__)
    auth = Auth(config)

    @bp.route("/studies", methods=["GET"])
    @auth.protected()
    def get_studies(user: User) -> Any:
        """
        Get Studies
        ---
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        tags:
          - Manage Studies
        """
        params = StorageServiceParameters(user=user)
        available_studies = storage_service.get_studies_information(params)
        return jsonify(available_studies), HTTPStatus.OK.value

    @bp.route("/studies", methods=["POST"])
    @auth.protected()
    def import_study(user: User) -> Any:
        """
        Import Study
        ---
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        tags:
          - Manage Studies
        """

        if "study" not in request.files:
            content = "No data provided."
            code = HTTPStatus.BAD_REQUEST.value
            return content, code

        zip_binary = io.BytesIO(request.files["study"].read())

        params = StorageServiceParameters(user=user)

        uuid = storage_service.import_study(zip_binary, params)
        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @bp.route(
        "/studies/<path:path>",
        methods=["GET"],
    )
    @auth.protected()
    def get_study(path: str, user: User) -> Any:
        """
        Read data
        ---
        responses:
          '200':
            description: Successful operation
            content:
              application/json: {}
          '404':
            description: File not found
        parameters:
          - in: path
            name: uuid
            required: true
            schema:
              type: string
          - in: path
            name: path
            schema:
              type: string
            required: true
        tags:
          - Manage Data inside Study
        """
        parameters = _construct_parameters(request.args, user)
        output = storage_service.get(path, parameters)

        return jsonify(output), 200

    @bp.route(
        "/studies/<string:uuid>/copy",
        methods=["POST"],
    )
    @auth.protected()
    def copy_study(uuid: str, user: User) -> Any:
        """
        Copy study
        ---
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        parameters:
        - in: path
          name: uuid
          required: true
          description: study uuid stored in server
          schema:
            type: string
        - in: query
          name: dest
          required: true
          description: new study name
          schema:
            type: string
        tags:
          - Manage Studies

        """

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

        params = StorageServiceParameters(user=user)

        destination_uuid = storage_service.copy_study(
            src_uuid=source_uuid_sanitized,
            dest_study_name=destination_name_sanitized,
            params=params,
        )
        content = "/studies/" + destination_uuid
        code = HTTPStatus.CREATED.value

        return content, code

    @bp.route(
        "/studies/<string:name>",
        methods=["POST"],
    )
    @auth.protected()
    def create_study(name: str, user: User) -> Any:
        """
        Create study name
        ---
        description: Create an empty study
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        parameters:
          - in: path
            name: name
            required: true
            description: study name asked
            schema:
              type: string
        tags:
          - Manage Studies
        """
        name_sanitized = sanitize_study_name(name)

        params = StorageServiceParameters(user=user)
        uuid = storage_service.create_study(name_sanitized, params)

        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @bp.route("/studies/<string:uuid>/export", methods=["GET"])
    @auth.protected()
    def export_study(uuid: str, user: User) -> Any:
        """
        Export Study
        ---
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        parameters:
        - in: path
          name: uuid
          required: true
          description: study uuid stored in server
          schema:
            type: string
        - in: query
          name: compact
          required: false
          example: false
          description: select compact format
          schema:
            type: boolean
        - in: query
          name: no-output
          required: false
          example: false
          description: specify
          schema:
            type: boolean
        tags:
          - Manage Studies
        """
        uuid_sanitized = sanitize_uuid(uuid)
        compact: bool = (
            "compact" in request.args and request.args["compact"] != "false"
        )
        outputs: bool = (
            "no-output" not in request.args
            or request.args["no-output"] == "false"
        )

        params = StorageServiceParameters(user=user)
        content = storage_service.export_study(
            uuid_sanitized, params, compact, outputs
        )

        return send_file(
            content,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"{uuid_sanitized}{'-compact' if compact else ''}.zip",
        )

    @bp.route("/studies/<string:uuid>", methods=["DELETE"])
    @auth.protected()
    def delete_study(uuid: str, user: User) -> Any:
        """
        Delete study
        ---
        responses:
          '200':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        parameters:
          - in: path
            name: uuid
            required: true
            description: study uuid used by server
            schema:
              type: string
        tags:
          - Manage Studies
        """
        uuid_sanitized = sanitize_uuid(uuid)

        params = StorageServiceParameters(user=user)
        storage_service.delete_study(uuid_sanitized, params)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @bp.route("/studies/<path:path>", methods=["POST"])
    @auth.protected()
    def edit_study(path: str, user: User) -> Any:
        """
        Update data
        ---
        responses:
          '200':
            description: Successful operation
            content:
              application/json: {}
          '404':
            description: File not found
        parameters:
          - in: path
            name: uuid
            required: true
            schema:
              type: string
          - in: path
            name: path
            schema:
              type: string
            required: true
        tags:
          - Manage Data inside Study
        """
        new = json.loads(request.data)
        if not new:
            raise BadRequest("empty body not authorized")

        params = StorageServiceParameters(user=user)
        storage_service.edit_study(path, new, params)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @bp.route(
        "/studies/<string:uuid>/output",
        methods=["POST"],
    )
    @auth.protected()
    def import_output(uuid: str, user: User) -> Any:
        """
        Import Output
        ---
        responses:
          '202':
            content:
              application/json: {}
            description: Successful operation
          '400':
            description: Invalid request
        parameters:
          - in: path
            name: uuid
            required: true
            description: study uuid used by server
            schema:
              type: string
        tags:
          - Manage Outputs
        """
        uuid_sanitized = sanitize_uuid(uuid)

        if "output" not in request.files:
            content = "No data provided."
            code = HTTPStatus.BAD_REQUEST.value
            return content, code

        zip_binary = io.BytesIO(request.files["output"].read())

        params = StorageServiceParameters(user=user)
        content = str(
            storage_service.import_output(uuid_sanitized, zip_binary, params)
        )
        code = HTTPStatus.ACCEPTED.value

        return jsonify(content), code

    return bp
