import sys
from pathlib import Path

from api_iso_antares.antares_io.reader import StudyReader, IniReader
from api_iso_antares.engine import UrlEngine
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server

if __name__ == "__main__":
    project_dir: Path = Path(__file__).resolve().parents[2]
    request_handler = RequestHandler(
        study_reader=StudyReader(reader_ini=IniReader()),
        url_engine=UrlEngine(),
        path_to_schema=Path(sys.argv[1]),
        path_to_study=Path(sys.argv[2]),
    )
    application = create_server(request_handler)

    application.run(debug=False, host="0.0.0.0", port=8080)
