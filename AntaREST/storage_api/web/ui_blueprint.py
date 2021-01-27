import io
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Tuple

from flask import Blueprint, request, render_template

from AntaREST.storage_api.web import RequestHandler
from AntaREST.storage_api.web.request_handler import RequestHandlerParameters


def wrap_status(fnc: Callable[[], Any]) -> str:
    try:
        fnc()
        return "ok"
    except Exception as e:
        print(e)
        return "error"


def create_ui(res: Path, request_handler: RequestHandler) -> Blueprint:
    bp = Blueprint(
        "create_ui",
        __name__,
        template_folder=str(res / "templates"),
    )

    @bp.route("/", methods=["GET", "POST"])
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

    @bp.route("/viewer/<path:path>", methods=["GET"])
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

    @bp.app_template_filter("date")  # type: ignore
    def time_filter(date: int) -> str:
        return datetime.fromtimestamp(date).strftime("%d-%m-%Y %H:%M")

    @bp.app_template_filter("trim_title")  # type: ignore
    def trim_title_filter(text: str) -> str:
        size = 30
        return text if len(text) < size else text[:size] + "..."

    @bp.app_template_filter("trim_id")  # type: ignore
    def trim_id_filter(text: str) -> str:
        size = 45
        return text if len(text) < size else text[:size] + "..."

    return bp
