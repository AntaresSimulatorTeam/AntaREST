import argparse
import os
import sys
import webbrowser
from datetime import timedelta
from numbers import Number
from pathlib import Path
from typing import Optional, Tuple, Any

from flask import Flask, render_template, json
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker, scoped_session  # type: ignore
from werkzeug.exceptions import HTTPException

from antarest import __version__
from antarest.common.config import ConfigYaml
from antarest.common.persistence import Base
from antarest.common.reverse_proxy import ReverseProxyMiddleware
from antarest.common.swagger import build_swagger
from antarest.login.main import build_login
from antarest.storage.main import build_storage


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        help="path to the config file",
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        help="Server version",
        action="store_true",
        required=False,
    )
    return parser.parse_args()


def get_arguments() -> Tuple[Optional[Path], bool]:
    arguments = parse_arguments()

    display_version = arguments.version or False
    if display_version:
        return Path("."), display_version

    config_file = Path(arguments.config_file)
    return config_file, display_version


def get_local_path() -> Path:
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except Exception:
        return Path(os.path.abspath(""))


def flask_app(config_file: Path) -> Flask:
    res = get_local_path() / "resources"
    config = ConfigYaml(res=res, file=config_file)

    # Database
    engine = create_engine(config["db.url"], echo=config["debug"])
    Base.metadata.create_all(engine)
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    application = Flask(
        __name__, static_url_path="/static", static_folder=str(res / "webapp")
    )
    application.wsgi_app = ReverseProxyMiddleware(application.wsgi_app)  # type: ignore
    application.config["SECRET_KEY"] = config["security.jwt.key"]
    application.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    application.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    application.config["JWT_TOKEN_LOCATION"] = ["headers"]

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
        return render_template("index.html")

    @application.teardown_appcontext
    def shutdown_session(exception: Any = None) -> None:
        db_session.remove()

    @application.errorhandler(HTTPException)
    def handle_exception(e: Any) -> Tuple[Any, Number]:
        """Return JSON instead of HTML for HTTP errors."""
        # start with the correct headers and status code from the error
        response = e.get_response()
        # replace the body with JSON
        response.data = json.dumps(
            {
                "name": e.name,
                "description": e.description,
            }
        )
        response.content_type = "application/json"
        return response, e.code

    build_storage(application, config)
    build_login(application, config, db_session)
    build_swagger(application)

    return application


if __name__ == "__main__":
    config_file, display_version = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()
    if config_file:
        flask_app(config_file).run(debug=False, host="0.0.0.0", port=8080)
    else:
        raise argparse.ArgumentError("Please provide the path for studies.")
