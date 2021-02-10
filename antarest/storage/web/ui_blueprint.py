import io
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Tuple

from flask import Blueprint, request, render_template, send_from_directory

from antarest.common.config import Config
from antarest.storage.web import RequestHandler
from antarest.storage.service import StorageServiceParameters


def get_local_path() -> Path:
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except Exception:
        return Path(os.path.abspath(""))


def wrap_status(fnc: Callable[[], Any]) -> str:
    try:
        fnc()
        return "ok"
    except Exception as e:
        print(e)
        return "error"


def create_ui(request_handler: RequestHandler, config: Config) -> Blueprint:
    bp = Blueprint(
        "create_ui",
        __name__,
        template_folder=str(config["main.res"] / "templates"),
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

        studies = request_handler.get_studies_information()
        return render_template(
            "home.html",
            studies=studies,
            size=len(studies),
            status=status,
            base_url=request.url_root,
        )

    @bp.route("/ui/static/<path:filename>")
    def serve_static_file(filename: Path) -> Any:
        static_folder = get_local_path() / "static"
        return send_from_directory(static_folder, filename)

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
        params = StorageServiceParameters(depth=1)
        info = request_handler.get_study_information(uuid=uuid)["antares"]

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
        return render_template(
            "study.html",
            info=info,
            id=uuid,
            data=data,
            base_url=request.url_root,
        )

    @bp.app_template_filter("date")  # type: ignore
    def time_filter(date: int) -> str:
        return datetime.fromtimestamp(date).strftime("%d-%m-%Y %H:%M")

    return bp
