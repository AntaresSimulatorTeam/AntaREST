import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from flask import Flask

from antarest import __version__
from antarest.common.reverse_proxy import ReverseProxyMiddleware
from antarest.common.swagger import build_swagger
from antarest.login.main import build_login
from antarest.storage_api.main import build_storage


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--studies",
        dest="studies_path",
        help="Path to the studies directory",
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

    arg_studies_path = arguments.studies_path
    studies_path = None
    if arg_studies_path is not None:
        studies_path = Path(arguments.studies_path)

    display_version = arguments.version or False

    return studies_path, display_version


def get_local_path() -> Path:
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except Exception:
        return Path(os.path.abspath(""))


def main(studies_path: Path) -> Flask:
    res = get_local_path() / "resources"
    application = Flask(__name__)
    application.wsgi_app = ReverseProxyMiddleware(application.wsgi_app)  # type: ignore
    application.config["SECRET_KEY"] = "super-secret"  # TODO strong password
    application.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]

    build_storage(application, res, studies_path)
    build_login(application, res)
    build_swagger(application)

    application.run(debug=False, host="0.0.0.0", port=8080)
    return application


if __name__ == "__main__":
    studies_path, display_version = get_arguments()

    if display_version:
        print(__version__)
        sys.exit()
    if studies_path is not None:
        main(studies_path)
    else:
        raise argparse.ArgumentError("Please provide the path for studies.")
