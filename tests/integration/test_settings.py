import json
from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import StudyReader, IniReader
from api_iso_antares.engine import UrlEngine
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


@pytest.mark.integration_test
def test_request(tmp_path: str) -> None:
    project_dir: Path = Path(__file__).resolve().parents[2]
    request_handler = RequestHandler(
        study_reader=StudyReader(reader_ini=IniReader()),
        url_engine=UrlEngine(),
        path_to_schema=project_dir / "api_iso_antares/jsonschema.json",
        path_to_study=project_dir / "tests/integration/study",
    )
    app = create_server(request_handler)
    client = app.test_client()
    res = client.get("/api/studies/settings/generaldata.ini/general/nbyears")
    assert json.loads(res.data) == 2
