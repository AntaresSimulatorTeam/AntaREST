import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from flask import Flask
from sqlalchemy import create_engine  # type: ignore

from antarest import __version__
from antarest.common.config import ConfigYaml
from antarest.common.dto import Base
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


def get_arguments() -> Tuple[Optional[Path], bool]:
    arguments = parse_arguments()

    config_file = Path(arguments.config_file)
    display_version = arguments.version or False

    return config_file, display_version


def get_local_path() -> Path:
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except Exception:
        return Path(os.path.abspath(""))


def main(config_file: Path) -> Flask:
    res = get_local_path() / "resources"
    config = ConfigYaml(res=res, file=config_file)

    # Database
    engine = create_engine(config["main.db.url"], echo=True)
    Base.metadata.create_all(engine)

    application = Flask(__name__)
    application.wsgi_app = ReverseProxyMiddleware(application.wsgi_app)  # type: ignore
    application.config["SECRET_KEY"] = config["main.jwt.key"]
    application.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]

    build_storage(application, config)
    build_login(application, config, engine)
    build_swagger(application)

    application.run(debug=False, host="0.0.0.0", port=8080)
    return application


if __name__ == "__main__":
    config_file, display_version = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()
    if config_file:
        main(config_file)
    else:
        raise argparse.ArgumentError("Please provide the path for studies.")
