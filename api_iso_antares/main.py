import json
import sys
from pathlib import Path

from api_iso_antares.antares_io.reader import (
    FolderReaderEngine,
    IniReader,
    JsmReader,
)
from api_iso_antares.antares_io.validator.jsonschema import JsmValidator
from api_iso_antares.engine import UrlEngine
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server

if __name__ == "__main__":
    project_dir: Path = Path(__file__).resolve().parents[2]
    jsonschema = JsmReader.read(Path(sys.argv[1]))
    request_handler = RequestHandler(
        study_reader=FolderReaderEngine(
            ini_reader=IniReader(),
            jsm=jsonschema,
            root=project_dir,
            jsm_validator=JsmValidator(jsm=jsonschema),
        ),
        url_engine=UrlEngine(jsm={}),
        path_studies=Path(sys.argv[2]),
    )
    application = create_server(request_handler)

    application.run(debug=False, host="0.0.0.0", port=8080)
