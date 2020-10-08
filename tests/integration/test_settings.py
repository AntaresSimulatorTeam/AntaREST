import json
from pathlib import Path

import pytest

from api_iso_antares.antares_io.reader import FolderReader, IniReader
from api_iso_antares.engine import UrlEngine
from api_iso_antares.web import RequestHandler
from api_iso_antares.web.server import create_server


@pytest.mark.integration_test
def test_request(tmp_path: str) -> None:

    project_dir: Path = Path(__file__).resolve().parents[2]

    path_to_schema = project_dir / "api_iso_antares/jsonschema.json"
    jsonschema = json.load(path_to_schema.open())

    request_handler = RequestHandler(
        study_reader=FolderReader(
            reader_ini=IniReader(), jsonschema=jsonschema
        ),
        url_engine=UrlEngine(jsonschema={}),
        path_to_studies=project_dir / "tests/integration",
    )

    app = create_server(request_handler)
    client = app.test_client()
    res = client.get("/api/studies/study/settings/generaldata.ini/general/nbyears")

    assert json.loads(res.data) == 2
