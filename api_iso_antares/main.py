import argparse
from pathlib import Path

from api_iso_antares.antares_io.reader import (
    IniReader,
    JsmReader,
)
from api_iso_antares.antares_io.validator import JsmValidator
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
    return parser.parse_args()


if __name__ == "__main__":
    arguments: argparse.Namespace = parse_arguments()

    jsm = JsmReader.read(Path(arguments.jsm_path))

    readers = {"default": IniReader()}
    study_reader = FileSystemEngine(jsm=jsm, readers=readers)

    request_handler = RequestHandler(
        study_parser=study_reader,
        url_engine=UrlEngine(jsm=jsm),
        path_studies=Path(arguments.studies_path),
        jsm_validator=JsmValidator(jsm=jsm),
    )
    application = create_server(request_handler)

    application.run(debug=False, host="0.0.0.0", port=8080)
