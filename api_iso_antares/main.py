import argparse
import os
import sys
from pathlib import Path

from api_iso_antares import __version__
from api_iso_antares.antares_io.exporter.export_file import Exporter
from api_iso_antares.antares_io.reader import (
    IniReader,
    JsmReader,
)
from api_iso_antares.antares_io.validator import JsmValidator
from api_iso_antares.antares_io.writer.ini_writer import IniWriter
from api_iso_antares.antares_io.writer.matrix_writer import MatrixWriter
from api_iso_antares.engine import UrlEngine
from api_iso_antares.engine.filesystem.engine import (
    FileSystemEngine,
)
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j",
        "--json-schema",
        dest="jsm_path",
        help="Path to the Json Schema file",
    )
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


def get_local_path() -> Path:
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return Path(sys._MEIPASS)  # type: ignore
    except Exception:
        return Path(os.path.abspath("."))


def main() -> None:
    arguments: argparse.Namespace = parse_arguments()

    if arguments.version:
        print(__version__)
        return

    jsm = JsmReader.read(Path(arguments.jsm_path))

    readers = {"default": IniReader()}
    writers = {"default": IniWriter(), "matrix": MatrixWriter()}
    study_parser = FileSystemEngine(jsm=jsm, readers=readers, writers=writers)

    request_handler = RequestHandler(
        study_parser=study_parser,
        url_engine=UrlEngine(jsm=jsm),
        exporter=Exporter(),
        path_studies=Path(arguments.studies_path),
        path_resources=get_local_path() / "resources",
        jsm_validator=JsmValidator(jsm=jsm),
    )
    application = create_server(request_handler)

    application.run(debug=False, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
