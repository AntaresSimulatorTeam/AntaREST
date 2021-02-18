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

from antarest.storage.web.html_exception import (
    HtmlException,
    stop_and_return_on_html_exception,
)
from antarest.storage.service import StorageServiceParameters, StorageService

storage_service: StorageService


def sanitize_uuid(uuid: str) -> str:
    return escape(uuid)


def sanitize_study_name(name: str) -> str:
    return sanitize_uuid(name)


def _construct_parameters(
    params: Any,
) -> StorageServiceParameters:
    request_parameters = StorageServiceParameters()
    request_parameters.depth = params.get(
        "depth", request_parameters.depth, type=int
    )
    return request_parameters


def create_study_routes(storage_service: StorageService) -> Blueprint:
    bp = Blueprint("create_study_route", __name__)

    @bp.route("/studies", methods=["GET"])
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
        available_studies = storage_service.get_studies_information()
        return jsonify(available_studies), HTTPStatus.OK.value

    @bp.route("/studies", methods=["POST"])
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

        uuid = storage_service.import_study(zip_binary)
        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @bp.route(
        "/studies/<path:path>",
        methods=["GET"],
    )
    @stop_and_return_on_html_exception
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
        tags:
          - Manage Data inside Study
        """
        parameters = _construct_parameters(request.args)
        output = storage_service.get(path, parameters)

        return jsonify(output), 200

    @bp.route(
        "/studies/<string:uuid>/copy",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
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

        destination_uuid = storage_service.copy_study(
            src_uuid=source_uuid_sanitized,
            dest_study_name=destination_name_sanitized,
        )
        content = "/studies/" + destination_uuid
        code = HTTPStatus.CREATED.value

        return content, code

    @bp.route(
        "/studies/<string:name>",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
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

        uuid = storage_service.create_study(name_sanitized)

        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @bp.route("/studies/<string:uuid>/export", methods=["GET"])
    @stop_and_return_on_html_exception
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
        compact: bool = "compact" in request.args and request.args["compact"]
        outputs: bool = (
            "no-output" not in request.args or not request.args["no-output"]
        )

        content = storage_service.export_study(
            uuid_sanitized, compact, outputs
        )

        return send_file(
            content,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"{uuid_sanitized}{'-compact' if compact else ''}.zip",
        )

    @bp.route("/studies/<string:uuid>", methods=["DELETE"])
    @stop_and_return_on_html_exception
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

        storage_service.delete_study(uuid_sanitized)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @bp.route("/studies/<path:path>", methods=["POST"])
    @stop_and_return_on_html_exception
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
            raise HtmlException("empty body not authorized", 400)

        storage_service.edit_study(path, new)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @bp.route(
        "/studies/<string:uuid>/output",
        methods=["POST"],
    )
    @stop_and_return_on_html_exception
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

        content = str(
            storage_service.import_output(uuid_sanitized, zip_binary)
        )
        code = HTTPStatus.ACCEPTED.value

        return jsonify(content), code

    return bp
