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

from antarest.login.auth import Auth
from antarest.common.config import Config
from antarest.storage.model import PublicMode
from antarest.storage.service import StorageService
from antarest.common.requests import (
    RequestParameters,
)


def sanitize_uuid(uuid: str) -> str:
    return str(escape(uuid))


def sanitize_study_name(name: str) -> str:
    return sanitize_uuid(name)


def create_study_routes(
    storage_service: StorageService, config: Config
) -> Blueprint:
    bp = Blueprint("create_study_route", __name__)
    auth = Auth(config)

    @bp.route("/studies", methods=["GET"])
    @auth.protected()
    def get_studies() -> Any:
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
        params = RequestParameters(user=Auth.get_current_user())
        available_studies = storage_service.get_studies_information(params)
        return jsonify(available_studies), HTTPStatus.OK.value

    @bp.route("/studies", methods=["POST"])
    @auth.protected()
    def import_study() -> Any:
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

        params = RequestParameters(user=Auth.get_current_user())

        uuid = storage_service.import_study(zip_binary, params)
        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @bp.route(
        "/studies/<path:path>",
        methods=["GET"],
    )
    @auth.protected()
    def get_study(path: str) -> Any:
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
          - in: query
            name: depth
            schema:
              type: string
        tags:
          - Manage Data inside Study
        """
        parameters = RequestParameters(user=Auth.get_current_user())
        depth = request.args.get("depth", 3, type=int)
        output = storage_service.get(path, depth, parameters)

        return jsonify(output), 200

    @bp.route(
        "/studies/<string:uuid>/copy",
        methods=["POST"],
    )
    @auth.protected()
    def copy_study(uuid: str) -> Any:
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

        params = RequestParameters(user=Auth.get_current_user())

        destination_uuid = storage_service.copy_study(
            src_uuid=source_uuid_sanitized,
            dest_study_name=destination_name_sanitized,
            params=params,
        )
        code = HTTPStatus.CREATED.value

        return destination_uuid, code

    @bp.route(
        "/studies/<string:name>",
        methods=["POST"],
    )
    @auth.protected()
    def create_study(name: str) -> Any:
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

        params = RequestParameters(user=Auth.get_current_user())
        uuid = storage_service.create_study(name_sanitized, params)

        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @bp.route("/studies/<string:uuid>/export", methods=["GET"])
    @auth.protected()
    def export_study(uuid: str) -> Any:
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
        outputs: bool = (
            "no-output" not in request.args
            or request.args["no-output"] == "false"
        )

        params = RequestParameters(user=Auth.get_current_user())
        content = storage_service.export_study(uuid_sanitized, params, outputs)

        return send_file(
            content,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"{uuid_sanitized}.zip",
        )

    @bp.route("/studies/<string:uuid>", methods=["DELETE"])
    @auth.protected()
    def delete_study(uuid: str) -> Any:
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

        params = RequestParameters(user=Auth.get_current_user())
        storage_service.delete_study(uuid_sanitized, params)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @bp.route("/studies/<path:path>", methods=["POST"])
    @auth.protected()
    def edit_study(path: str) -> Any:
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

        params = RequestParameters(user=Auth.get_current_user())
        storage_service.edit_study(path, new, params)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @bp.route(
        "/studies/<string:uuid>/output",
        methods=["POST"],
    )
    @auth.protected()
    def import_output(uuid: str) -> Any:
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

        params = RequestParameters(user=Auth.get_current_user())
        content = str(
            storage_service.import_output(uuid_sanitized, zip_binary, params)
        )
        code = HTTPStatus.ACCEPTED.value

        return jsonify(content), code

    @bp.route(
        "/studies/<string:uuid>/owner/<int:user_id>",
        methods=["PUT"],
    )
    @auth.protected()
    def change_owner(uuid: str, user_id: int) -> Any:
        """
        Change study owner
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
          - in: path
            name: user_id
            required: true
            description: id of the new owner
            schema:
              type: number
        tags:
          - Manage Permissions
        """
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=Auth.get_current_user())
        storage_service.change_owner(uuid_sanitized, user_id, params)

        return "", HTTPStatus.OK

    @bp.route(
        "/studies/<string:uuid>/groups/<string:group_id>",
        methods=["PUT"],
    )
    @auth.protected()
    def add_group(uuid: str, group_id: str) -> Any:
        """
        Add a group association
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
          - in: path
            name: group_id
            required: true
            description: id of the group to add
            schema:
              type: string
        tags:
          - Manage Permissions
        """
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=Auth.get_current_user())
        storage_service.add_group(uuid_sanitized, group_id, params)

        return "", HTTPStatus.OK

    @bp.route(
        "/studies/<string:uuid>/groups/<string:group_id>",
        methods=["DELETE"],
    )
    @auth.protected()
    def remove_group(uuid: str, group_id: str) -> Any:
        """
        Remove a group association
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
          - in: path
            name: group_id
            required: true
            description: id of the group to remove
            schema:
              type: string
        tags:
          - Manage Permissions
        """
        uuid_sanitized = sanitize_uuid(uuid)

        params = RequestParameters(user=Auth.get_current_user())
        storage_service.remove_group(uuid_sanitized, group_id, params)

        return "", HTTPStatus.OK

    @bp.route(
        "/studies/<string:uuid>/public_mode/<string:mode>",
        methods=["PUT"],
    )
    @auth.protected()
    def set_public_mode(uuid: str, mode: str) -> Any:
        """
        Set study public mode
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
          - in: path
            name: mode
            required: true
            description: public mode
            schema:
              type: string
              enum: [NONE,READ,EXECUTE,EDIT,FULL]
        tags:
          - Manage Permissions
        """
        uuid_sanitized = sanitize_uuid(uuid)
        params = RequestParameters(user=Auth.get_current_user())
        public_mode = PublicMode(mode)
        storage_service.set_public_mode(uuid_sanitized, public_mode, params)

        return "", HTTPStatus.OK

    return bp
