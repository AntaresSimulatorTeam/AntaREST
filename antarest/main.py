import argparse
import logging
import os
import sys
from numbers import Number
from pathlib import Path
from typing import Tuple, Any

from gevent import monkey  # type: ignore

from antarest.login.config import get_config as get_security_config

monkey.patch_all()

from flask import Flask, render_template, json, request
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker, scoped_session  # type: ignore
from werkzeug.exceptions import HTTPException

from antarest import __version__, login
from antarest.eventbus.main import build_eventbus
from antarest.login.auth import Auth
from antarest.common.config import ConfigYaml, Config
from antarest.common.persistence import Base
from antarest.common.reverse_proxy import ReverseProxyMiddleware
from antarest.common.swagger import build_swagger
from antarest.launcher.main import build_launcher
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


def get_default_config_path() -> Path:
    config = Path("config.yaml")
    if config.exists():
        return config

    config = Path.home() / ".antares/config.yaml"
    if config.exists():
        return config

    raise ValueError(
        "Config file not found. Set it by '-c' with command line or place it at ./config.yaml or ~/.antares/config.yaml"
    )


def get_arguments() -> Tuple[Path, bool]:
    arguments = parse_arguments()

    display_version = arguments.version or False
    if display_version:
        return Path("."), display_version

    config_file = Path(arguments.config_file or get_default_config_path())
    return config_file, display_version


def get_local_path() -> Path:
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except Exception:
        return Path(os.path.abspath(""))


def configure_logger(config: Config) -> None:
    logging_path = config["logging.path"]
    logging_level = (
        config["logging.level"]
        if config["logging.level"] is not None
        else "INFO"
    )
    logging_format = (
        config["logging.format"]
        if config["logging.format"] is not None
        else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.basicConfig(
        filename=logging_path, format=logging_format, level=logging_level
    )


def flask_app(config_file: Path) -> Flask:
    res = get_local_path() / "resources"
    config = ConfigYaml(res=res, file=config_file)

    configure_logger(config)
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

    application.config["SECRET_KEY"] = get_security_config(config).jwt.key
    application.config["JWT_ACCESS_TOKEN_EXPIRES"] = Auth.ACCESS_TOKEN_DURATION
    application.config[
        "JWT_REFRESH_TOKEN_EXPIRES"
    ] = Auth.REFRESH_TOKEN_DURATION
    application.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]

    @application.route("/", methods=["GET"])
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
        Auth.invalidate()
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

    event_bus = build_eventbus(application, config)
    storage = build_storage(
        application, config, db_session, event_bus=event_bus
    )
    build_launcher(
        application,
        config,
        db_session,
        service_storage=storage,
        event_bus=event_bus,
    )
    build_login(application, config, db_session, event_bus=event_bus)
    build_swagger(application)

    return application


if __name__ == "__main__":
    config_file, display_version = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()
    else:
        app = flask_app(config_file)
        app.socketio.run(app, debug=False, host="0.0.0.0", port=8080)
