import io
import json
import os
import re
import subprocess
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any, Optional, Callable, Tuple

from flask import (
    escape,
    Flask,
    jsonify,
    request,
    Response,
    send_file,
    render_template,
)
from flask_swagger import swagger  # type: ignore
from flask_swagger_ui import get_swaggerui_blueprint  # type: ignore

from storage_api import __version__
from storage_api.web.html_exception import (
    HtmlException,
    stop_and_return_on_html_exception,
)
from storage_api.web.request_handler import (
    RequestHandler,
    RequestHandlerParameters,
)
from storage_api.web.swagger import update

request_handler: RequestHandler


def sanitize_uuid(uuid: str) -> str:
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


def wrap_status(fnc: Callable[[], Any]) -> str:
    try:
        fnc()
        return "ok"
    except Exception as e:
        print(e)
        return "error"


def create_ui_routes(application: Flask) -> None:
    @application.route("/", methods=["GET", "POST"])
    def home() -> Any:
        """
        Home ui
        ---
        responses:
            '200':
              content:
                 application/html: {}
              description: html home page
        tags:
          - UI
        """
        status = ""

        if request.method == "POST":
            print(request.form)
            print(request.files)
            if "name" in request.form:
                status = wrap_status(
                    fnc=lambda: request_handler.create_study(
                        request.form["name"]
                    )
                )

            elif "delete-id" in request.form:  # DELETE
                status = wrap_status(
                    fnc=lambda: request_handler.delete_study(
                        request.form.get("delete-id", "")
                    )
                )

            elif "study" in request.files:
                zip_binary = io.BytesIO(request.files["study"].read())
                status = wrap_status(
                    fnc=lambda: request_handler.import_study(zip_binary)
                )

        studies = request_handler.get_studies_informations()
        return render_template(
            "home.html", studies=studies, size=len(studies), status=status
        )

    @application.route("/viewer/<path:path>", methods=["GET"])
    def display_study(path: str) -> Any:
        def set_item(
            sub_path: str, name: str, value: Any
        ) -> Tuple[str, str, str]:
            if isinstance(value, str) and "file/" in value:
                return "link", name, f"/{value}"
            elif isinstance(value, (str, int, float)):
                return "data", name, str(value)
            else:
                return "folder", name, f"/viewer/{sub_path}/{name}/"

        parts = path.split("/")
        uuid, selections = parts[0], parts[1:]
        params = RequestHandlerParameters(depth=1)
        info = request_handler.get_study_informations(uuid=uuid)["antares"]

        # [
        #  (selected, [(type, name, url), ...]),
        # ]
        data = []
        print(request_handler.get(path, params))
        for i, part in enumerate(selections):
            sub_path = "/".join([uuid] + selections[:i])
            items = [
                set_item(sub_path, name, value)
                for name, value in request_handler.get(
                    sub_path, params
                ).items()
            ]
            data.append((part, items))
        return render_template("study.html", info=info, id=uuid, data=data)

    @application.template_filter("date")  # type: ignore
    def time_filter(date: int) -> str:
        return datetime.fromtimestamp(date).strftime("%d-%m-%Y %H:%M")

    @application.template_filter("trim_title")  # type: ignore
    def trim_title_filter(text: str) -> str:
        size = 30
        return text if len(text) < size else text[:size] + "..."

    @application.template_filter("trim_id")  # type: ignore
    def trim_id_filter(text: str) -> str:
        size = 45
        return text if len(text) < size else text[:size] + "..."


def create_study_routes(application: Flask) -> None:
    @application.route("/studies", methods=["GET"])
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
        global request_handler
        available_studies = request_handler.get_studies_informations()
        return jsonify(available_studies), HTTPStatus.OK.value

    @application.route("/studies", methods=["POST"])
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
        global request_handler

        if "study" not in request.files:
            content = "No data provided."
            code = HTTPStatus.BAD_REQUEST.value
            return content, code

        zip_binary = io.BytesIO(request.files["study"].read())

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
        global request_handler

        name_sanitized = sanitize_study_name(name)

        uuid = request_handler.create_study(name_sanitized)

        content = "/studies/" + uuid
        code = HTTPStatus.CREATED.value

        return jsonify(content), code

    @application.route("/studies/<string:uuid>/export", methods=["GET"])
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
        global request_handler

        uuid_sanitized = sanitize_uuid(uuid)
        compact: bool = "compact" in request.args
        outputs: bool = "no-output" not in request.args

        content = request_handler.export_study(
            uuid_sanitized, compact, outputs
        )

        return send_file(
            content,
            mimetype="application/zip",
            as_attachment=True,
            attachment_filename=f"{uuid_sanitized}{'-compact' if compact else ''}.zip",
        )

    @application.route("/studies/<string:uuid>", methods=["DELETE"])
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
        global request_handler

        uuid_sanitized = sanitize_uuid(uuid)

        request_handler.delete_study(uuid_sanitized)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @application.route("/studies/<path:path>", methods=["POST"])
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
        global request_handler

        new = json.loads(request.data)
        if not new:
            raise HtmlException("empty body not authorized", 400)

        request_handler.edit_study(path, new)
        content = ""
        code = HTTPStatus.NO_CONTENT.value

        return content, code

    @application.route(
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
        global request_handler
        uuid_sanitized = sanitize_uuid(uuid)

        if "output" not in request.files:
            content = "No data provided."
            code = HTTPStatus.BAD_REQUEST.value
            return content, code

        zip_binary = io.BytesIO(request.files["output"].read())

        content = str(
            request_handler.import_output(uuid_sanitized, zip_binary)
        )
        code = HTTPStatus.ACCEPTED.value

        return jsonify(content), code


def create_non_business_routes(application: Flask) -> None:
    swaggerui_blueprint = get_swaggerui_blueprint(
        "/docs",
        "/swagger.json",
        config={"app_name": "Test application", "validatorUrl": None},
    )
    application.register_blueprint(swaggerui_blueprint)

    @application.route(
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
        global request_handler

        data = request.files["matrix"].read()
        request_handler.upload_matrix(path, data)
        output = b""
        code = HTTPStatus.NO_CONTENT.value

        return output, code

    @application.route(
        "/swagger.json",
        methods=["GET"],
    )
    def spec() -> Any:
        spec = update(swagger(application))
        spec["servers"] = [{"url": request.host_url}]

        return jsonify(spec)

    @application.route("/health", methods=["GET"])
    def health() -> Any:
        return jsonify({"status": "available"}), 200

    @application.route("/version", methods=["GET"])
    def version() -> Any:
        global request_handler

        version_data = {"version": __version__}
        commit_id = get_commit_id(request_handler.path_resources)
        if commit_id is not None:
            version_data["gitcommit"] = commit_id

        return jsonify(version_data), HTTPStatus.OK.value

    @application.after_request
    def after_request(response: Response) -> Response:
        header = response.headers
        header["Access-Control-Allow-Origin"] = "*"
        return response


def create_routes(application: Flask) -> None:
    create_study_routes(application)
    create_non_business_routes(application)
    create_ui_routes(application)


def create_server(req: RequestHandler, res: Path) -> Flask:
    global request_handler
    request_handler = req
    print(Path(os.curdir).absolute())
    application = Flask(__name__, template_folder=str(res / "templates"))
    create_routes(application)
    return application
